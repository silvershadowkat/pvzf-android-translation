# Third-party projects and attribution

- **Dobby** by jmpews and contributors, Apache-2.0:
  <https://github.com/jmpews/Dobby>, commit
  `21f07a5ce184cda9346afb8009c07fe7e47390d0`.
  Statically linked into the new prerelease 3 English runtime for both Android
  ARM architectures. The source is unmodified. Its license and source pin are
  included in `assets/english/NOTICE.txt` in the APK. This version is pinned
  because its Android build works with the documented toolchain.

- **Plants vs. Zombies Fusion translation data**  -
  <https://github.com/Teyliu/PVZF-Translation>, licensed CC BY-NC 4.0.
- **PVZFusionTranslation source**  -
  <https://github.com/Teyliu/PVZFusionTranslation>.
- **PVZ Hyper Fusion Mod** by ArifRios1st  -
  <https://github.com/ArifRios1st/PVZ-Hyper-Fusion-Mod>, credited by the PC
  translator as its original mod predecessor.
- **il2cpp-stringliteral-patcher** by József Sallai  -
  <https://github.com/jozsefsallai/il2cpp-stringliteral-patcher>, MIT. Its
  documented metadata layout and append-and-redirect technique informed the
  independent deterministic builder in this repository.
- **UnityPy**  -  <https://github.com/K0lb3/UnityPy>, used by the optional Unity
  asset inspection scripts under its own license.
- **TypeTreeGeneratorAPI**  -
  <https://github.com/UnityPy-Org/TypeTreeGeneratorAPI>, used for managed Unity
  type-tree generation under its own license.
- **MelonLoader Audio Tools** by TrevTV  -
  <https://github.com/TrevTV/MelonLoader-AudioTools>, credited by the upstream
  PC translator; not bundled by this Android toolkit.
- **Apktool**  -  <https://github.com/iBotPeaches/Apktool>, used for local APK
  inspection under its own license. The prerelease 3 packager makes structured
  application-identity edits to Android resources; it does not use Apktool to
  recompile the game.

No third-party game binaries or translation datasets are included here.
