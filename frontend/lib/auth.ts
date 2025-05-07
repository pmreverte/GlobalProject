import { jwtVerify } from "jose";

export async function verifyAuth(token: string): Promise<boolean> {
  if (!token) return false;
  
  try {
    const secret = new TextEncoder().encode(process.env.NEXT_PUBLIC_JWT_SECRET_KEY || 'defaultsecret');
    await jwtVerify(token, secret);
    return true;
  } catch (error) {
    console.error('Error verifying token:', error);
    return false;
  }
}