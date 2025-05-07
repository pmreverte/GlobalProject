# AI-Powered Document Query System

## Project Overview
This is a full-stack application that combines document management, SQL querying, and AI capabilities. The system allows users to upload documents, perform intelligent queries, and manage configurations through an admin interface.

## Prerequisites
- Python 3.8+
- Node.js 16+
- SQL Server with ODBC Driver 17
- Git
- OpenAI API key or other LLM provider key

## Environment Setup

### Global Environment Variables
Create a `.env` file in the root directory with:
```bash
# SQL Server Configuration
SQL_SERVER_URL=mssql+pyodbc://YOUR_SERVER/YOUR_DB?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes

# LLM Configuration
LLM_API_KEY=your_llm_api_key
LLM_MODEL=gpt-4  # or gpt-3.5-turbo

# JWT Authentication
JWT_SECRET_KEY=your_secure_secret_key
JWT_ALGORITHM=HS256
JWT_EXP_MINUTES=60

# File Storage Paths
UPLOAD_FOLDER=./uploads
VECTORSTORE_PATH=./vectorstore/documents
```

### Backend Configuration

1. SQL Server Configuration (`config/sql_config.json`):
```json
{
  "server": "YOUR_SERVER_NAME",
  "database": "YOUR_DATABASE_NAME",
  "username": "YOUR_USERNAME",  // Leave empty if using Windows authentication
  "password": "YOUR_PASSWORD",  // Leave empty if using Windows authentication
  "driver": "ODBC Driver 17 for SQL Server",
  "use_windows_auth": true  // Set to false if using SQL authentication
}
```

2. LLM Configuration (`config/llm_config.yaml`):
Create this file if it doesn't exist. This will be configured through the admin interface.

### Frontend Environment Variables

Create a `.env.local` file in the frontend directory with:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_JWT_SECRET_KEY=your_secure_secret_key  # Should match JWT_SECRET_KEY in global .env
```

## Architecture

### Frontend (Next.js)
- Built with Next.js 13+
- Uses TypeScript for type safety
- Tailwind CSS for styling
- Components organized in:
  - `/app`: Page components and API routes
  - `/components`: Reusable UI components
  - `/lib`: Utility functions and API helpers

### Backend (Python/FastAPI)
- FastAPI for REST API implementation
- Modular architecture with:
  - `/api`: Route handlers for different functionalities
  - `/auth`: Authentication and user management
  - `/core`: Core business logic
  - `/db`: Database interactions
  - `/documents`: Document processing
  - `/llms`: Language Model integration
  - `/sql`: SQL query handling
  - `/utils`: Utility functions

## Installation & Setup

### Backend Setup
1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python backend/db/init_db.py
```

5. Create admin user:
```bash
python backend/auth/create_admin_user.py
```

6. Start the backend server:
```bash
python backend/main.py
```

### Frontend Setup
1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

## Project Structure
```
├── backend/
│   ├── api/           # API route handlers
│   ├── auth/          # Authentication system
│   ├── core/          # Core business logic
│   ├── db/            # Database operations
│   ├── documents/     # Document processing
│   ├── llms/          # LLM integration
│   ├── sql/           # SQL query handling
│   └── utils/         # Utility functions
├── frontend/
│   ├── app/          # Next.js pages
│   ├── components/   # React components
│   ├── lib/          # Utility functions
│   └── styles/       # CSS styles
├── config/           # Configuration files
├── uploads/          # Document storage
└── vectorstore/      # Vector embeddings
```

## Key Features

### Authentication System
- JWT-based authentication
- Role-based access control
- User management through admin interface

### Document Management
- Document upload and processing
- Vector store integration for semantic search
- Document indexing and retrieval

### Query System
- SQL query execution with RAG integration
- Natural language query processing
- Query analytics and logging

### Admin Interface
- User management
- LLM configuration
- SQL server configuration
- Document processing settings
- Analytics and reporting

## API Documentation

### Authentication Endpoints
- `POST /api/auth/login`: User authentication
- `POST /api/auth/verify`: Token verification

### Admin Routes
- `GET /api/admin/users`: List users
- `POST /api/admin/users`: Create user
- `PUT /api/admin/users/{username}`: Update user
- `DELETE /api/admin/users/{username}`: Delete user

### Document Routes
- `POST /api/documents/upload`: Upload document
- `GET /api/documents`: List documents
- `DELETE /api/documents/{id}`: Delete document

### Query Routes
- `POST /api/query`: Execute query
- `GET /api/query/history`: Get query history
- `POST /api/query/feedback`: Submit query feedback

## Security Considerations
- JWT-based authentication
- Role-based access control
- SQL injection prevention
- Document validation
- API rate limiting

## Development Guidelines
- Use TypeScript for frontend development
- Follow PEP 8 for Python code
- Document all API endpoints
- Write unit tests for critical functionality
- Use proper error handling

## Troubleshooting

### Common Issues
1. SQL Server Connection:
   - Ensure SQL Server is running
   - Verify Windows authentication or credentials
   - Check ODBC Driver 17 is installed

2. Backend Server:
   - Verify virtual environment is activated
   - Check all dependencies are installed
   - Ensure ports are not in use

3. Frontend Development:
   - Verify Node.js version
   - Check .env.local configuration
   - Clear Next.js cache if needed

4. LLM Integration:
   - Verify LLM_API_KEY is valid
   - Check selected model availability
   - Ensure proper API endpoint configuration

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
[Add your license here]