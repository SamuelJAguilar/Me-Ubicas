# Me Ubicas

Juego de adivina quién para dos personas, en el mismo móvil. Se turnan el celular para crear personajes y adivinar el del otro.

## Cómo se juega

1. **Crear personajes.** Agrega foto, nombre y características: ojos, pelo, piel, sexo, edad, bello facial y accesorios (lentes, aretes, gorras, etc.). Cada una es una clasificación con elementos (por ejemplo pelo: Negro y Rubio). Puedes crear uno nuevo, como Blanco, si tu personaje lo necesita.
2. **Jugar.** El juego toma hasta 20 personajes al azar para cada jugador. No tienen que ser los mismos si hay más de 20.
3. El jugador 1 elige su personaje secreto y pasa el celular. El jugador 2 hace lo mismo.
4. En tu turno ves los 20 del otro jugador. Preguntas una clasificación, por ejemplo pelo blanco. El juego responde si el personaje secreto lo tiene o no. Tachar o reactivar fichas es criterio tuyo: el juego no descarta por ti.
5. Lo que ya preguntaste (ese elemento, no toda la clasificación) no vuelve a salir en tus turnos siguientes. No hay límite de tiempo.
6. **Descartar** permite tachar y también reactivar a alguien tachado antes. **Adivinar** acierta o te hace perder el turno. **Listo** pasa el celular.

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
flet run src/main.py
```

En una ventana de tamaño móvil:

```bash
flet run src/main.py
```

Para Android, con el SDK configurado:

```bash
flet build apk
```

Al abrir la app por primera vez se cargan 4 personajes de ejemplo (Goku, Naruto, Jack y Shiro) usando las imágenes de `Imagenes/`, para poder probar de inmediato.
