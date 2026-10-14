
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("access_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export async function loginUser(username, password) {
  const formData = new URLSearchParams();

  formData.append("username", username);
  formData.append("password", password);
  formData.append("grant_type", "password");

  const response = await api.post("/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  sessionStorage.setItem("access_token", response.data.access_token);

  return response.data;
}

export default api;
