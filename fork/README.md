# Fork de N4ML355 — FFNY Online para Linux (Wine)

Este fork añade **dos cosas** y nada más; todo lo demás es idéntico al repo oficial
(`sweeax-exe/ffny-online`, que se queda como `upstream`):

1. `fork/patch-wine.py`: desactiva el rechazo de Wine del instalador de Windows
   (`setup/main.cpp`, la función `runningUnderWine()` pasa a devolver `false`).
2. `.github/workflows/fork-wine-build.yml`: cada día (o a mano, en la pestaña
   *Actions* → **Run workflow**) sincroniza `main` con el repo oficial, aplica el
   parche **solo en el checkout de CI** (nunca se confirma al repo), compila el
   instalador de Windows y lo publica en el release **`wine-latest`**.

Por qué es así: el parche vive fuera del código fuente, así que cada
sincronización con el repo oficial es un merge limpio y la verificación de Wine
**nunca vuelve a activarse por sí sola**, aunque el repo oficial cambie esa zona.

## Cómo usarlo

1. **Descargar**: pestaña *Releases* → `wine-latest` → `DefJamSetup-*.exe`.
2. **Instalar bajo Wine** (prefix propio, DXVK recomendado):

   ```
   wine DefJamSetup-<versión>-windows-x64.exe --silent \
        --dump C:\\ruta\\tu-dump.xiso \
        --install-dir C:\\Games\\FFNYOnline \
        --data-dir C:\\Games\\FFNYOnline\\data \
        --install-prerequisites
   ```

   o simplemente doble clic para el asistente gráfico.

3. **No aceptes actualizaciones dentro del juego**: el launcher del juego baja el
   setup **oficial**, que vuelve a traer el chequeo de Wine. Antes de jugar:

   ```
   setx RECOMP_NO_UPDATE_CHECK 1
   ```

   (una sola vez; desactiva el aviso de actualización del launcher) y descarga
   las versiones nuevas solo desde el release `wine-latest` de este fork.

4. **Online**: no se tocó nada del juego ni de los servidores; juegas en los
   mismos relays oficiales con tu amigo. Ten en cuenta que el juego compara
   `LOCKSTEP_VERSION` y el build: para jugar online ambos deben tener el mismo
   build, así que tu amigo y tú deberíais estar en el mismo `remaster.N`.

## Aviso técnico

El instalador no trae el juego precompilado (no se puede distribuir): lo
construye desde **tu propio dump**. En Windows usa MSVC Build Tools + CMake +
Ninja; con `--install-prerequisites` el propio setup los instala, pero bajo Wine
puede que tengas que provisionar el toolchain en el prefix a mano. Si el build
te pide algo que no está, es eso, no el parche de Wine.

## Sincronizar a mano (opcional)

```
git remote add upstream https://github.com/sweeax-exe/ffny-online.git
git fetch upstream main
git merge upstream/main
git push origin main
```

El workflow también lo hace solo cada día. Si algún día el repo oficial mueve o
reescribe `runningUnderWine()`, el paso "The Wine patch still applies" del
workflow fallará en rojo: solo hay que ajustar `fork/patch-wine.py`.
