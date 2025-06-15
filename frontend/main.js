// Cambia esta URL por la de tu API en Render
const API_URL = "https://portfolio-ecommerce.onrender.com";
let accessToken = null;
let userEmail = null;

function showLoading(btn, loading) {
  if (loading) {
    btn.disabled = true;
    btn.textContent = 'Cargando...';
  } else {
    btn.disabled = false;
    btn.textContent = btn.dataset.originalText;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Si ya hay token, muestra el formulario de pedidos
  if (accessToken) {
    document.getElementById("pedido-form").style.display = "block";
    document.getElementById("login-form").style.display = "none";
  }
});

function login() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const btn = document.querySelector('#login-form button');
  btn.dataset.originalText = btn.textContent;

  // Validación básica
  if (!email.match(/^\S+@\S+\.\S+$/)) {
    document.getElementById("login-error").textContent = "Introduce un email válido.";
    return;
  }
  if (!password || password.length < 4) {
    document.getElementById("login-error").textContent = "Introduce una contraseña válida.";
    return;
  }
  document.getElementById("login-error").textContent = "";
  showLoading(btn, true);

  fetch(`${API_URL}/api/users/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
      showLoading(btn, false);
      if (status === 200 && data.access) {
        accessToken = data.access;
        userEmail = email;
        document.getElementById("login-form").style.display = "none";
        document.getElementById("pedido-form").style.display = "block";
        document.getElementById("login-error").textContent = "";
        document.getElementById("user-info").style.display = "block";
        document.getElementById("user-info").textContent = `Usuario logueado: ${userEmail}`;
        // Limpiar campos
        document.getElementById("email").value = "";
        document.getElementById("password").value = "";
      } else {
        document.getElementById("login-error").textContent = data.detail || "Error de autenticación";
      }
    })
    .catch(() => {
      showLoading(btn, false);
      document.getElementById("login-error").textContent = "Error de red";
    });
}

function crearPedido() {
  const productos = document.getElementById("productos").value.split(",").map(x => x.trim());
  const cantidades = document.getElementById("cantidades").value.split(",").map(x => parseInt(x.trim()));
  const btn = document.querySelector('#pedido-form button');
  btn.dataset.originalText = btn.textContent;

  // Validación
  if (productos.length === 0 || cantidades.length === 0 || productos.some(x => !x) || cantidades.some(isNaN)) {
    document.getElementById("pedido-error").textContent = "IDs y cantidades deben ser números válidos.";
    return;
  }
  if (productos.length !== cantidades.length) {
    document.getElementById("pedido-error").textContent = "IDs y cantidades deben coincidir.";
    return;
  }
  if (cantidades.some(q => q <= 0)) {
    document.getElementById("pedido-error").textContent = "Las cantidades deben ser mayores que cero.";
    return;
  }
  document.getElementById("pedido-error").textContent = "";
  showLoading(btn, true);

  const items = productos.map((id, i) => ({ product_id: parseInt(id), quantity: cantidades[i] }));
  fetch(`${API_URL}/api/orders/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${accessToken}`
    },
    body: JSON.stringify({ items })
  })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
      showLoading(btn, false);
      if (status === 200 && data.id) {
        document.getElementById("pedido-success").textContent = `Pedido creado con ID: ${data.id}`;
        document.getElementById("pedido-error").textContent = "";
        // Limpiar campos
        document.getElementById("productos").value = "";
        document.getElementById("cantidades").value = "";
      } else {
        document.getElementById("pedido-error").textContent = data.detail || "Error al crear pedido";
        document.getElementById("pedido-success").textContent = "";
      }
    })
    .catch(() => {
      showLoading(btn, false);
      document.getElementById("pedido-error").textContent = "Error de red";
      document.getElementById("pedido-success").textContent = "";
    });
}
