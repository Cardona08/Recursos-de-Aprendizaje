// Seleccionamos los botones
const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.getElementById('container');

// Cuando clicas en “Registrarse”, activa la clase
signUpButton.addEventListener('click', () => {
  container.classList.add('right-panel-active');
});

// Cuando clicas en “Iniciar Sesión”, la desactiva
signInButton.addEventListener('click', () => {
  container.classList.remove('right-panel-active');
});
document.getElementById("btnEntrar").addEventListener("click", function(event) {
    event.preventDefault(); // evita que recargue la página
    window.location.href = "Inicio.html"; // cambia a tu página
});
document.getElementByUp("btnEntrar").addEventListener("click", function(event) {
    event.preventDefault(); // evita que recargue la página
    window.location.href = "Inicio.html"; // cambia a tu página
});

