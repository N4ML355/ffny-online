# Fork de N4ML355 — FFNY Online para Linux (Wine)

Este fork añade **dos cosas** y nada más; todo lo demás es idéntico al repo oficial
(`sweeax-exe/ffny-online`, que se queda como `upstream`):

1. `fork/patch-wine.py`: desactiva el rechazo de Wine del instalador de Windows
   (`setup/main.cpp`, `runningUnderWine()` pasa a devolver `false`).
2. El mismo parche hace que `startEngine()` detecte Wine y **entregue el payload**
   (ya descomprimido y verificado) al puente **`wine-update-bridge.exe`** de
   [`ffny-linux-updater`](https://github.com/N4ML355/ffny-linux-updater), que
   compila el juego en Linux con llvm-mingw y escribe los recibos de instalación.
   El setup ya no intenta ejecutar MSVC/PowerShell bajo Wine.
3. `.github/workflows/fork-wine-build.yml`: cada día (o a mano, en la pestaña
   *Actions* → **Run workflow**) sincroniza `main` con el repo oficial, aplica el
   parche **solo en el checkout de CI** (nunca se confirma al repo), compila el
   instalador de Windows y lo publica en el release **`wine-latest`**.

Por qué es así: el parche vive fuera del código fuente, así que cada
sincronización con el repo oficial es un merge limpio y la verificación de Wine
**nunca vuelve a activarse por sí sola**, aunque el repo oficial cambie esa zona.

## Cómo se encuentra el puente

`startEngine()` busca `wine-update-bridge.exe` en este orden:

1. `FFNY_BRIDGE` (variable de entorno, ruta Windows).
2. Junto al `DefJamSetup-*.exe`.
3. `<carpeta del setup>\ffny-tools\`.
4. El directorio actual y `.\ffny-tools\`.
5. `<install-dir>\..\..\ffny-tools\` (la ubicación que usa el launcher para
   actualizarse solo).

Si no lo encuentra, el setup falla con un mensaje que explica qué instalar; nunca
cae de vuelta en MSVC.

## Instalar desde cero

1. Prepara las herramientas en la carpeta desde la que ejecutarás el setup
   (recomendado: la misma que usará luego el launcher, `<padre>/ffny-tools`):

   ```bash
   git clone https://github.com/N4ML355/ffny-linux-updater.git
   cd ffny-linux-updater
   ./setup.sh --tools-dir "$HOME/Games/FFNY Online/ffny-tools"
   ```

2. Descarga el `DefJamSetup-*.exe` de este release (`wine-latest`) y cópialo
   dentro de esa carpeta `ffny-tools`.

3. Ejecútalo con el prefix que vayas a usar (los paths son Windows, del prefix):

   ```bash
   export TOOLS="$HOME/Games/FFNY Online/ffny-tools"
   export WINEPREFIX="$HOME/Games/prefixes/defjam"
   wine "$TOOLS/DefJamSetup-<versión>-windows-x64.exe" --silent \
        --dump "/ruta/a/tu/dump.xiso" \
        --install-dir 'C:\Games\FFNY Online\app' \
        --data-dir 'C:\Games\FFNY Online\data'
   ```

   o doble clic para el asistente gráfico: el wizard muestra el progreso normal
   (texto/barra) mientras Linux compila.

4. Configura el actualizador para la nueva instalación:

   ```bash
   cd ffny-linux-updater
   ./setup.sh --install-dir "$WINEPREFIX/drive_c/Games/FFNY Online/app"
   ```

5. En Lutris, apunta el juego a `.../FFNY Online/app/DefJamLauncher.exe`.

## Actualizar

- Desde la terminal: `ffny-tools/ffny-update`.
- Desde el launcher: su botón de actualización descarga el setup **oficial** y lo
  lanza; el setup oficial no arranca en Wine. Mantén
  `setx RECOMP_NO_UPDATE_CHECK 1` y actualiza con `ffny-update` (o vuelve a
  descargar `wine-latest`). No aceptes el setup oficial dentro del juego.

## Online

No se tocó nada del juego ni de los servidores; juegas en los mismos relays
oficiales. El juego compara `LOCKSTEP_VERSION` y el build: para jugar online ambos
jugadores deben tener el mismo `remaster.N`.

## Aviso técnico

El setup no trae el juego precompilado (no se puede distribuir): lo construye
desde tu propio dump. En Windows usa MSVC Build Tools + CMake + Ninja; **bajo Wine
siempre delega en el puente Linux** (aunque hubiera MSVC en el prefix), y requiere
que `ffny-linux-updater` haya preparado antes su toolchain y su venv.

## Sincronizar a mano (opcional)

```
git remote add upstream https://github.com/sweeax-exe/ffny-online.git
git fetch upstream main
git merge upstream/main
git push origin main
```

El workflow también lo hace solo cada día. Si algún día el repo oficial cambia
`runningUnderWine()` o `startEngine()`, el paso "The Wine patch still applies" del
workflow fallará en rojo: solo hay que ajustar `fork/patch-wine.py`.
