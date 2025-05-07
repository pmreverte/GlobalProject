# Documentación del Sistema de Consultas con IA Multifuente

## Descripción General del Proyecto

El Sistema de Consultas con IA Multifuente es una aplicación full-stack que combina gestión de documentos, consultas SQL y capacidades de inteligencia artificial. El sistema permite a los usuarios cargar documentos, realizar consultas inteligentes utilizando lenguaje natural y gestionar configuraciones a través de una interfaz de administración.

La aplicación utiliza tecnologías modernas como FastAPI para el backend, Next.js para el frontend, y modelos de lenguaje avanzados para procesar consultas en lenguaje natural. El sistema implementa un enfoque de Generación Aumentada por Recuperación (RAG) para proporcionar respuestas contextualizadas basadas en documentos y datos SQL.

## Estructura del Proyecto

El proyecto sigue una arquitectura clara dividida en frontend y backend:

```
├── backend/                # Servidor FastAPI
│   ├── api/                # Manejadores de rutas API
│   ├── auth/               # Sistema de autenticación
│   ├── core/               # Lógica de negocio principal
│   ├── db/                 # Operaciones de base de datos
│   ├── documents/          # Procesamiento de documentos
│   ├── llms/               # Integración con modelos de lenguaje
│   ├── logs/               # Sistema de registro
│   ├── models/             # Modelos de datos
│   ├── sql/                # Manejo de consultas SQL
│   ├── tests/              # Pruebas unitarias
│   ├── utils/              # Funciones de utilidad
│   └── main.py             # Punto de entrada de la aplicación
├── frontend/               # Aplicación Next.js
│   ├── app/                # Páginas y rutas
│   ├── components/         # Componentes reutilizables
│   ├── lib/                # Utilidades y helpers de API
│   └── styles/             # Estilos CSS
├── config/                 # Archivos de configuración
├── uploads/                # Almacenamiento de documentos
└── vectorstore/            # Almacenamiento de embeddings vectoriales
```

### Componentes Principales

1. **Backend (FastAPI)**:
   - Proporciona una API RESTful para todas las funcionalidades
   - Implementa autenticación basada en JWT
   - Gestiona el procesamiento de documentos y consultas
   - Integra modelos de lenguaje para procesamiento de lenguaje natural

2. **Frontend (Next.js)**:
   - Interfaz de usuario moderna y responsiva
   - Implementado con TypeScript para seguridad de tipos
   - Utiliza Tailwind CSS para estilos
   - Componentes modulares para diferentes funcionalidades

3. **Almacenamiento de Vectores**:
   - Utiliza FAISS para almacenar y buscar embeddings vectoriales
   - Permite búsquedas semánticas en documentos

4. **Sistema de Autenticación**:
   - Control de acceso basado en roles
   - Tokens JWT para autenticación
   - Gestión de usuarios y permisos

## Clases y Funciones Principales

### Backend

#### Sistema de Autenticación (`auth_system.py`)

**Clase `Token`**
- **Propósito**: Modelo de respuesta para tokens de autenticación.
- **Atributos**:
  - `access_token`: Token JWT de acceso
  - `token_type`: Tipo de token (siempre "bearer")

**Clase `UserBase`**
- **Propósito**: Modelo base para respuestas de usuario.
- **Atributos**:
  - `username`: Nombre de usuario
  - `role`: Rol del usuario en el sistema

**Función `get_user(username: str, db: Session) -> DBUser`**
- **Propósito**: Recuperar un usuario de la base de datos por nombre de usuario.
- **Parámetros**:
  - `username`: Nombre de usuario a buscar
  - `db`: Sesión de base de datos
- **Retorno**: Objeto de usuario si se encuentra, None en caso contrario
- **Lógica**: Consulta la base de datos para encontrar un usuario por nombre de usuario

**Función `authenticate_user(username: str, password: str, db: Session) -> DBUser`**
- **Propósito**: Autenticar un usuario con nombre de usuario y contraseña.
- **Parámetros**:
  - `username`: Nombre de usuario a autenticar
  - `password`: Contraseña a verificar
  - `db`: Sesión de base de datos
- **Retorno**: Objeto de usuario autenticado si es exitoso, None en caso contrario
- **Lógica**: Verifica las credenciales del usuario contra la base de datos

**Función `create_access_token(data: dict, expires_delta: timedelta = None) -> str`**
- **Propósito**: Crear un nuevo token de acceso JWT.
- **Parámetros**:
  - `data`: Datos a codificar en el token
  - `expires_delta`: Tiempo de expiración del token (opcional)
- **Retorno**: Token JWT codificado
- **Lógica**: Genera un token JWT con los datos proporcionados y tiempo de expiración

#### Procesamiento de Documentos (`doc_indexer.py`)

**Función `create_document_record(db: Session, filepath: str, user_id: int) -> DocumentRecord`**
- **Propósito**: Crear un nuevo registro de documento en la base de datos.
- **Parámetros**:
  - `db`: Sesión de base de datos
  - `filepath`: Ruta al archivo del documento
  - `user_id`: ID del usuario que carga el documento
- **Retorno**: Registro de documento creado
- **Lógica**: Crea un registro en la base de datos y registra la acción

**Función `procesar_archivo(ruta: str) -> List[Document]`**
- **Propósito**: Procesar un archivo y extraer su contenido.
- **Parámetros**:
  - `ruta`: Ruta al archivo a procesar
- **Retorno**: Lista de documentos LangChain con contenido extraído
- **Lógica**: Utiliza cargadores específicos según el tipo de archivo (PDF, Word)

**Función `cargar_y_indexar_documentos(directorio: str, user_id: int, recursivo: bool = False, db: Session = None) -> Tuple[str, List[str]]`**
- **Propósito**: Cargar e indexar documentos desde un directorio.
- **Parámetros**:
  - `directorio`: Ruta del directorio con documentos
  - `user_id`: ID del usuario que carga documentos
  - `recursivo`: Si se deben procesar subdirectorios
  - `db`: Sesión de base de datos
- **Retorno**: Mensaje de estado y lista de archivos procesados
- **Lógica**: Valida, carga documentos, divide texto en fragmentos, genera embeddings y almacena en índice FAISS

**Función `recuperar_contexto_desde_documentos(pregunta: str, k: int = 5) -> str`**
- **Propósito**: Recuperar contexto relevante de documentos indexados.
- **Parámetros**:
  - `pregunta`: Consulta para buscar
  - `k`: Número de fragmentos relevantes a recuperar
- **Retorno**: Contexto combinado de fragmentos de documentos relevantes
- **Lógica**: Utiliza búsqueda de similitud FAISS para encontrar fragmentos de texto relevantes

#### Utilidades RAG SQL (`rag_sql_utils.py`)

**Función `convertir_resultado_a_texto(resultado: Dict, incluir_similares: bool = True) -> str`**
- **Propósito**: Convertir resultados de consulta SQL a formato de texto legible.
- **Parámetros**:
  - `resultado`: Resultados de consulta SQL
  - `incluir_similares`: Si se deben incluir registros similares
- **Retorno**: Representación de texto formateada de los resultados
- **Lógica**: Formatea los resultados SQL y opcionalmente enriquece con registros similares

**Función `generar_respuesta_con_contexto(pregunta: str, contexto: str, llm_id: int = None) -> str`**
- **Propósito**: Generar una respuesta en lenguaje natural usando contexto y un LLM.
- **Parámetros**:
  - `pregunta`: Pregunta del usuario
  - `contexto`: Información de contexto (resultados SQL)
  - `llm_id`: ID de configuración LLM específico a usar
- **Retorno**: Respuesta generada en lenguaje natural
- **Lógica**: Combina el contexto con la pregunta para generar una respuesta coherente

### Frontend

**Componente `ChatBox.tsx`**
- **Propósito**: Interfaz de chat para interactuar con el sistema.
- **Funcionalidad**: Permite a los usuarios enviar consultas y ver respuestas.

**Componente `DocumentUpload.tsx`**
- **Propósito**: Interfaz para cargar documentos al sistema.
- **Funcionalidad**: Permite a los usuarios seleccionar y cargar archivos.

**Componente `FeedbackRespuesta.tsx`**
- **Propósito**: Recopilar retroalimentación sobre las respuestas generadas.
- **Funcionalidad**: Permite a los usuarios calificar la calidad de las respuestas.

## Dependencias

### Backend (Python)

- **FastAPI**: Framework web para crear APIs con Python
- **Uvicorn**: Servidor ASGI para ejecutar aplicaciones FastAPI
- **SQLAlchemy**: ORM para interactuar con bases de datos
- **LangChain**: Framework para aplicaciones basadas en LLM
- **OpenAI**: Cliente para acceder a modelos de OpenAI
- **Anthropic**: Cliente para acceder a modelos de Anthropic
- **FAISS-CPU**: Biblioteca para búsqueda de similitud eficiente
- **PyODBC**: Conector para bases de datos SQL Server
- **Python-Jose**: Implementación de JWT para autenticación
- **Passlib**: Biblioteca para hashing de contraseñas
- **Python-Multipart**: Soporte para formularios multipart
- **Python-dotenv**: Carga de variables de entorno
- **Pytest**: Framework para pruebas unitarias

### Frontend (JavaScript/TypeScript)

- **Next.js**: Framework React para aplicaciones web
- **React**: Biblioteca para construir interfaces de usuario
- **TypeScript**: Superset tipado de JavaScript
- **Axios**: Cliente HTTP para realizar peticiones
- **Tailwind CSS**: Framework CSS utilitario
- **JWT-Decode**: Decodificación de tokens JWT
- **Radix UI**: Componentes de interfaz accesibles
- **Lucide React**: Iconos para la interfaz

## Flujo de Trabajo y Arquitectura

El sistema implementa una arquitectura de microservicios con separación clara entre frontend y backend:

1. **Flujo de Autenticación**:
   - El usuario inicia sesión a través de la interfaz web
   - El backend valida las credenciales y emite un token JWT
   - El token se almacena en el cliente y se usa para autenticar solicitudes posteriores

2. **Flujo de Procesamiento de Documentos**:
   - El usuario carga documentos a través de la interfaz
   - El backend procesa los documentos, extrae texto y genera embeddings
   - Los embeddings se almacenan en un índice FAISS para búsqueda semántica

3. **Flujo de Consulta**:
   - El usuario envía una consulta en lenguaje natural
   - El sistema determina si la consulta requiere acceso a documentos, SQL o ambos
   - Para consultas SQL, se genera y ejecuta una consulta SQL
   - Para consultas de documentos, se recupera contexto relevante
   - El LLM genera una respuesta coherente basada en el contexto recuperado

4. **Arquitectura RAG (Retrieval-Augmented Generation)**:
   - Recuperación: Busca información relevante en documentos y bases de datos
   - Aumento: Enriquece el contexto con información recuperada
   - Generación: Utiliza un LLM para generar respuestas basadas en el contexto

```
[Usuario] → [Frontend] → [API Backend] → [Router de Consultas]
                                           ↓
                                         [Determinar Tipo de Consulta]
                                           ↓
                           ┌───────────────┴───────────────┐
                           ↓                               ↓
                     [Procesador SQL]               [Procesador de Documentos]
                           ↓                               ↓
                     [Ejecutar SQL]                  [Búsqueda Vectorial]
                           ↓                               ↓
                     [Resultados SQL]               [Contexto de Documentos]
                           ↓                               ↓
                           └───────────────┬───────────────┘
                                           ↓
                                     [Generador LLM]
                                           ↓
                                     [Respuesta]
                                           ↓
                                     [Usuario]
```

## Instrucciones de Instalación y Configuración

### Requisitos Previos

- Python 3.9+ instalado
- Node.js 16+ instalado
- Acceso a una base de datos SQL (opcional para funcionalidades SQL)
- Claves API para servicios de LLM (OpenAI, Anthropic)

### Configuración del Backend

1. **Crear entorno virtual**:
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Unix/MacOS:
   source venv/bin/activate
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**:
   Crear un archivo `.env` en la raíz del proyecto con:
   ```
   JWT_SECRET_KEY=your_secret_key
   LLM_API_KEY=your_openai_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   DATABASE_URL=your_database_connection_string
   ```

4. **Inicializar la base de datos**:
   ```bash
   python backend/db/init_db.py
   ```

5. **Crear usuario administrador**:
   ```bash
   python backend/auth/create_admin_user.py
   ```

6. **Iniciar el servidor backend**:
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

### Configuración del Frontend

1. **Instalar dependencias**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configurar variables de entorno**:
   Crear un archivo `.env.local` en el directorio `frontend` con:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Iniciar el servidor de desarrollo**:
   ```bash
   npm run dev
   ```

### Configuración para Producción

1. **Construir el frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Ejecutar el backend con Gunicorn**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app
   ```

3. **Configurar un servidor web (Nginx/Apache) para servir el frontend y hacer proxy al backend**

## Testing y Validación

El proyecto incluye un conjunto completo de pruebas unitarias para validar la funcionalidad del sistema:

### Estructura de Pruebas

- **Pruebas Unitarias**: Validan componentes individuales
- **Pruebas de Integración**: Validan la interacción entre componentes
- **Pruebas End-to-End**: Validan flujos completos de usuario

### Ejecutar Pruebas

```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar pruebas con cobertura
pytest --cov=backend

# Ejecutar pruebas específicas
pytest backend/tests/test_auth_system.py
```

### Herramientas de Prueba

- **Pytest**: Framework principal de pruebas
- **Pytest-cov**: Análisis de cobertura de código
- **unittest.mock**: Simulación de componentes para pruebas aisladas

## Errores Comunes y Solución de Problemas

### Problemas de Autenticación

**Error**: "Credenciales incorrectas" al iniciar sesión
- **Solución**: Verificar que el nombre de usuario y contraseña sean correctos
- **Solución**: Ejecutar `python backend/auth/create_admin_user.py` para restablecer el usuario administrador

**Error**: "Token expirado" o "Token inválido"
- **Solución**: Cerrar sesión y volver a iniciar sesión para obtener un nuevo token
- **Solución**: Verificar que `JWT_SECRET_KEY` sea consistente en el entorno

### Problemas de Procesamiento de Documentos

**Error**: "No se encontraron documentos válidos"
- **Solución**: Verificar que los documentos tengan una extensión permitida (.pdf, .doc, .docx)
- **Solución**: Verificar que los documentos no excedan el tamaño máximo configurado

**Error**: "Error al eliminar documento del vectorstore"
- **Solución**: Verificar que el documento existe en el sistema
- **Solución**: Reiniciar el servidor si el índice vectorial está corrupto

### Problemas de Consultas SQL

**Error**: "Error de conexión a la base de datos"
- **Solución**: Verificar que la cadena de conexión en `DATABASE_URL` sea correcta
- **Solución**: Verificar que el servidor de base de datos esté accesible

**Error**: "Error de sintaxis SQL"
- **Solución**: Revisar los logs para ver la consulta generada
- **Solución**: Ajustar la configuración del LLM para mejorar la generación de SQL

### Problemas de LLM

**Error**: "API key not valid"
- **Solución**: Verificar que `LLM_API_KEY` contenga una clave API válida
- **Solución**: Verificar que la cuenta asociada tenga créditos disponibles

**Error**: "Respuestas vacías o incompletas"
- **Solución**: Ajustar los parámetros de temperatura y longitud máxima en la configuración LLM
- **Solución**: Verificar que el contexto proporcionado sea suficiente y relevante

## Licencia y Derechos de Autor

### Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulte el archivo LICENSE para más detalles.

### Derechos de Autor

© 2023-2024 Todos los derechos reservados.

### Contribuciones

Las contribuciones al proyecto son bienvenidas. Por favor, siga estas pautas:

1. Bifurque el repositorio
2. Cree una rama para su característica (`git checkout -b feature/amazing-feature`)
3. Confirme sus cambios (`git commit -m 'Add some amazing feature'`)
4. Envíe a la rama (`git push origin feature/amazing-feature`)
5. Abra una Pull Request

### Agradecimientos

- LangChain por proporcionar el framework para aplicaciones basadas en LLM
- OpenAI y Anthropic por sus modelos de lenguaje avanzados
- La comunidad de FastAPI y Next.js por sus excelentes herramientas y documentación