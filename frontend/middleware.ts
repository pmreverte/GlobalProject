import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { jwtDecode } from 'jwt-decode'

interface TokenData {
  sub: string;
  role: string;
  exp: number;
}

// Rutas que no requieren autenticación
const publicRoutes = ['/login', '/']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // No aplicar middleware a rutas públicas
  if (publicRoutes.includes(pathname)) {
    return NextResponse.next()
  }


  // Obtener el token de la cookie
  const token = request.cookies.get('token')?.value

  // Si no hay token, redirigir a login
  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  try {
    const decoded = jwtDecode<TokenData>(token)
    const currentTime = Math.floor(Date.now() / 1000)

    // Verificar campos requeridos del token
    if (!decoded.sub || !decoded.role || !decoded.exp) {
      console.error('Token malformado:', decoded)
      const response = NextResponse.redirect(new URL('/login', request.url))
      response.cookies.delete('token')
      return response
    }

    // Verificar si el token ha expirado
    if (decoded.exp < currentTime) {
      console.error('Token expirado:', {
        expTime: new Date(decoded.exp * 1000).toISOString(),
        currentTime: new Date(currentTime * 1000).toISOString()
      })
      const response = NextResponse.redirect(new URL('/login', request.url))
      response.cookies.delete('token')
      return response
    }

    // Verificar permisos para rutas administrativas
    if (pathname.startsWith('/admin') && decoded.role !== 'superuser') {
      console.error('Acceso denegado a ruta admin:', {
        path: pathname,
        role: decoded.role
      })
      return NextResponse.redirect(new URL('/', request.url))
    }

    return NextResponse.next()
  } catch (error) {
    console.error('Error al validar token:', error)
    const response = NextResponse.redirect(new URL('/login', request.url))
    response.cookies.delete('token')
    return response
  }
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}