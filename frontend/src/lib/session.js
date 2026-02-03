export function getToken() {
  return localStorage.getItem("token");
}

export function setToken(token) {
  localStorage.setItem("token", token);
}

export function clearToken() {
  localStorage.removeItem("token");
}

export function setSession({ token, role, user_id, name }) {
  localStorage.setItem("token", token);
  localStorage.setItem("role", role);
  localStorage.setItem("user_id", String(user_id));
  localStorage.setItem("name", name);
}

export function getRole() {
  return localStorage.getItem("role");
}

export function getUserId() {
  const v = localStorage.getItem("user_id");
  return v ? Number(v) : null;
}

export function getName() {
  return localStorage.getItem("name");
}

export function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("user_id");
  localStorage.removeItem("name");
}
