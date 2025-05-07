"""
Analytics API Routes Module

This module provides endpoints for retrieving and analyzing system usage data,
including query statistics, user activity, and performance metrics.

Features:
- Report generation and export
- Usage analytics
- Performance metrics
- User activity tracking
- Feedback analysis

All routes require superuser privileges and provide detailed insights
into system usage and performance.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Optional
from ..db.database import get_db
from ..auth.dependencies import require_role
from ..auth.models import User
from ..models.analytics import Query
from sqlalchemy import func, and_
from sqlalchemy.orm import joinedload

from fastapi.responses import Response
import csv
from io import StringIO

# Initialize router with prefix and tag
router = APIRouter(prefix="/admin", tags=["Analíticas"])

@router.get("/reports/export")
async def export_reports(
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    current_user=Depends(require_role("superuser")),
    db: Session = Depends(get_db)
):
    """
    Export query reports as CSV file.
    
    This endpoint generates a downloadable CSV file containing
    query logs within the specified date range.
    
    Args:
        startDate (str, optional): Start date for filtering (ISO format)
        endDate (str, optional): End date for filtering (ISO format)
        
    Returns:
        Response: CSV file containing query reports
        
    Raises:
        HTTPException: If date format is invalid or export fails
        
    Note:
        CSV includes: user, query, response, feedback, and timestamp
    """
    try:
        # Base query with user join
        query = db.query(Query).options(joinedload(Query.user)).order_by(Query.timestamp.desc())

        # Apply date filters if provided
        if startDate and endDate:
            start = datetime.fromisoformat(startDate.replace('Z', '+00:00'))
            end = datetime.fromisoformat(endDate.replace('Z', '+00:00'))
            query = query.filter(
                and_(
                    Query.timestamp >= start,
                    Query.timestamp <= end
                )
            )

        # Execute query
        results = query.all()

        # Create CSV file in memory
        output = StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(['Usuario', 'Consulta', 'Respuesta', 'Feedback', 'Fecha'])

        # Write data
        for q in results:
            writer.writerow([
                q.user.username if q.user else "Unknown",
                q.query,
                q.response,
                q.feedback,
                q.timestamp.isoformat()
            ])

        # Prepare response
        response = Response(
            content=output.getvalue(),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = f"attachment; filename=reports_{datetime.now().strftime('%Y%m%d')}.csv"
        
        return response

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error en el formato de fecha: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al exportar informes: {str(e)}"
        )

@router.get("/reports")
async def get_reports(
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    current_user=Depends(require_role("superuser")),
    db: Session = Depends(get_db)
):
    """
    Get query reports in JSON format.
    
    This endpoint returns detailed query logs with optional date filtering.
    
    Args:
        startDate (str, optional): Start date for filtering (ISO format)
        endDate (str, optional): End date for filtering (ISO format)
        
    Returns:
        List[dict]: List of query reports with detailed information
        
    Raises:
        HTTPException: If date format is invalid or query fails
        
    Note:
        Each report includes:
        - Query details
        - Response information
        - Feedback
        - Performance metrics
        - User information
    """
    try:
        # Base query with user join
        query = db.query(Query).options(joinedload(Query.user)).order_by(Query.timestamp.desc())

        # Apply date filters if provided
        if startDate and endDate:
            start = datetime.fromisoformat(startDate.replace('Z', '+00:00'))
            end = datetime.fromisoformat(endDate.replace('Z', '+00:00'))
            query = query.filter(
                and_(
                    Query.timestamp >= start,
                    Query.timestamp <= end
                )
            )

        # Execute query and format results
        results = query.all()
        return [
            {
                "id": q.id,
                "query": q.query,
                "response": q.response,
                "feedback": q.feedback,
                "topic": q.topic,
                "response_time": q.response_time,
                "timestamp": q.timestamp.isoformat(),
                "user": q.user.username if q.user else "Unknown"
            }
            for q in results
        ]

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error en el formato de fecha: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener informes: {str(e)}"
        )

@router.get("/analytics")
async def get_analytics(
    range: str = "week",
    current_user=Depends(require_role("superuser")),
    db: Session = Depends(get_db)
):
    """
    Get system analytics and metrics.
    
    This endpoint provides comprehensive analytics including:
    - Total query count
    - Average response time
    - User activity statistics
    - Feedback distribution
    - Query trends over time
    - Popular topics
    
    Args:
        range (str): Time range for analytics
            Options: "week", "month", "year"
            Default: "week"
            
    Returns:
        dict: Analytics data including:
            - totalQueries: Total number of queries
            - averageResponseTime: Average response time in seconds
            - userStats: Top users by query count
            - feedbackStats: Distribution of feedback
            - queryCountByDate: Query trends over time
            - topTopics: Most common query topics
            
    Raises:
        HTTPException: If analytics calculation fails
        
    Note:
        This endpoint aggregates multiple metrics to provide
        a comprehensive view of system usage and performance.
    """
    # Calculate date range
    now = datetime.utcnow()
    if range == "week":
        start_date = now - timedelta(days=7)
    elif range == "month":
        start_date = now - timedelta(days=30)
    elif range == "year":
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=7)  # default to week

    try:
        # Get total queries
        total_queries = db.query(func.count()).select_from(Query).scalar() or 0

        # Get average response time
        avg_response_time = db.query(
            func.avg(Query.response_time)
        ).scalar() or 0.0

        # Get user stats
        user_stats = (
            db.query(
                Query.user_id,
                User.username,
                func.count().label("query_count")
            )
            .join(User)
            .group_by(Query.user_id, User.username)
            .order_by(func.count().desc())
            .limit(5)
            .all()
        )

        # Get feedback stats
        feedback_stats = {
            "positive": db.query(func.count())
            .filter(Query.feedback == "positive")
            .scalar() or 0,
            "negative": db.query(func.count())
            .filter(Query.feedback == "negative")
            .scalar() or 0,
            "neutral": db.query(func.count())
            .filter(Query.feedback == "neutral")
            .scalar() or 0,
        }

        # Get query count by date
        query_count_by_date = (
            db.query(
                func.date(Query.timestamp).label("date"),
                func.count().label("count")
            )
            .filter(Query.timestamp >= start_date)
            .group_by(func.date(Query.timestamp))
            .order_by(func.date(Query.timestamp))
            .all()
        )

        # Get top topics
        top_topics = (
            db.query(
                Query.topic,
                func.count().label("count")
            )
            .filter(Query.topic.isnot(None))
            .group_by(Query.topic)
            .order_by(func.count().desc())
            .limit(5)
            .all()
        )

        return {
            "totalQueries": total_queries,
            "averageResponseTime": float(avg_response_time),
            "userStats": [
                {"username": stat.username, "queryCount": stat.query_count}
                for stat in user_stats
            ],
            "feedbackStats": feedback_stats,
            "queryCountByDate": [
                {"date": str(stat.date), "count": stat.count}
                for stat in query_count_by_date
            ],
            "topTopics": [
                {"topic": stat.topic, "count": stat.count}
                for stat in top_topics
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener analíticas: {str(e)}"
        )