"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import api from "@/lib/api";
import { AxiosError } from "axios";

interface User {
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [newUser, setNewUser] = useState({
    username: "",
    full_name: "",
    password: "",
    role: "user"
  });
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await api.get("/api/admin/users");
      setUsers(response.data);
    } catch (error) {
      setError("Error al cargar usuarios");
      if (error instanceof AxiosError && error.response?.status === 401) {
        window.location.href = '/login';
      }
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post("/api/admin/users", newUser);
      setSuccess("Usuario creado exitosamente");
      setNewUser({ username: "", full_name: "", password: "", role: "user" });
      fetchUsers();
    } catch (error) {
      if (error instanceof AxiosError) {
        setError(error.response?.data?.error || "Error al crear usuario");
      } else {
        setError("Error al crear usuario");
      }
    }
  };

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;

    try {
      await api.put(`/api/admin/users/${editingUser.username}`, editingUser);
      setSuccess("Usuario actualizado exitosamente");
      setEditingUser(null);
      fetchUsers();
    } catch (error) {
      if (error instanceof AxiosError) {
        setError(error.response?.data?.error || "Error al actualizar usuario");
      } else {
        setError("Error al actualizar usuario");
      }
    }
  };

  const handleDeleteUser = async (username: string) => {
    if (!confirm("¿Está seguro de eliminar este usuario?")) return;

    try {
      await api.delete(`/api/admin/users/${username}`);
      setSuccess("Usuario eliminado exitosamente");
      fetchUsers();
    } catch (error) {
      if (error instanceof AxiosError) {
        setError(error.response?.data?.error || "Error al eliminar usuario");
      } else {
        setError("Error al eliminar usuario");
      }
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Gestión de Usuarios</h1>

      {/* Mensajes de error y éxito */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          {success}
        </div>
      )}

      {/* Formulario para crear nuevo usuario */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h2 className="text-xl font-semibold mb-4">Crear Nuevo Usuario</h2>
        <form onSubmit={handleCreateUser} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre de Usuario
            </label>
            <Input
              type="text"
              value={newUser.username}
              onChange={(e) =>
                setNewUser({ ...newUser, username: e.target.value })
              }
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre Completo
            </label>
            <Input
              type="text"
              value={newUser.full_name}
              onChange={(e) =>
                setNewUser({ ...newUser, full_name: e.target.value })
              }
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña
            </label>
            <Input
              type="password"
              value={newUser.password}
              onChange={(e) =>
                setNewUser({ ...newUser, password: e.target.value })
              }
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Rol
            </label>
            <select
              className="border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring focus:border-blue-500"
              value={newUser.role}
              onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
            >
              <option value="user">Usuario</option>
              <option value="superuser">Superusuario</option>
            </select>
          </div>
          <Button type="submit">Crear Usuario</Button>
        </form>
      </div>

      {/* Lista de usuarios */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Usuarios Existentes</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Usuario
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nombre Completo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.username}>
                  <td className="px-6 py-4 whitespace-nowrap">{user.username}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{user.full_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{user.role}</td>
                  <td className="px-6 py-4 whitespace-nowrap space-x-2">
                    <Button
                      onClick={() => setEditingUser(user)}
                      className="bg-yellow-600 hover:bg-yellow-700"
                    >
                      Editar
                    </Button>
                    <Button
                      onClick={() => handleDeleteUser(user.username)}
                      className="bg-red-600 hover:bg-red-700"
                    >
                      Eliminar
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal de edición */}
      {editingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg w-96">
            <h2 className="text-xl font-semibold mb-4">Editar Usuario</h2>
            <form onSubmit={handleUpdateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre Completo
                </label>
                <Input
                  type="text"
                  value={editingUser.full_name}
                  onChange={(e) =>
                    setEditingUser({ ...editingUser, full_name: e.target.value })
                  }
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Rol
                </label>
                <select
                  className="border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring focus:border-blue-500"
                  value={editingUser.role}
                  onChange={(e) =>
                    setEditingUser({ ...editingUser, role: e.target.value })
                  }
                >
                  <option value="user">Usuario</option>
                  <option value="superuser">Superusuario</option>
                </select>
              </div>
              <div className="flex justify-end space-x-2">
                <Button
                  type="button"
                  className="bg-gray-600 hover:bg-gray-700"
                  onClick={() => setEditingUser(null)}
                >
                  Cancelar
                </Button>
                <Button type="submit">Guardar Cambios</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}