from fastapi import APIRouter, Depends, Body, HTTPException
from backend.sql.sql_connector import ejecutar_query
from backend.auth.dependencies import require_role
from backend.llms.llm_manager import generar_sql_desde_pregunta
from backend.sql.rag_sql_utils import convertir_resultado_a_texto, generar_respuesta_con_contexto
from backend.logs.logger import registrar_consulta
from backend.sql.sql_embeddings import get_similar_records

router = APIRouter(prefix="/query", tags=["Consultas"])

@router.post("/preguntar")
def preguntar_sql(
    pregunta: str = Body(...),
    current_user=Depends(require_role("user"))
):
    try:
        # Paso 1: Buscar en embeddings primero
        registros_similares = get_similar_records(pregunta, k=10)
        if registros_similares:
            # Si encontramos registros similares, usar esos como contexto
            contexto = "Información encontrada en la base de datos:\n"
            for registro in registros_similares:
                contexto += f"- {registro['content']}\n"
            
            # Generar respuesta usando el contexto de embeddings
            respuesta = generar_respuesta_con_contexto(pregunta, contexto)
            
            # Registrar consulta en logs
            registrar_consulta(
                usuario=current_user.username,
                pregunta=pregunta,
                sql="Consulta respondida usando embeddings",
                resultado={"embeddings": registros_similares},
                respuesta=respuesta
            )
            
            return {
                "respuesta": respuesta,
                "sql_generado": "Consulta respondida usando embeddings"
            }

        # Si no hay resultados en embeddings, proceder con SQL
        sql = generar_sql_desde_pregunta(pregunta)
        resultado = ejecutar_query(sql)
        if "error" in resultado:
            raise HTTPException(status_code=400, detail=resultado["error"])

        contexto = convertir_resultado_a_texto(resultado, incluir_similares=False)
        respuesta = generar_respuesta_con_contexto(pregunta, contexto)

        registrar_consulta(
            usuario=current_user.username,
            pregunta=pregunta,
            sql=sql,
            resultado=resultado,
            respuesta=respuesta
        )

        return {
            "respuesta": respuesta,
            "sql_generado": sql
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
