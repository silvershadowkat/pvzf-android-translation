# Third-party projects and attribution

- **OpenAI CLIP**, MIT: <https://github.com/openai/CLIP>. The experimental AI APK uses the ViT-B/32 vision tower exported to float32 ONNX. Model provenance and hashes are recorded in the export manifest, and the MIT license is packaged as `assets/plantbrush/CLIP-LICENSE.txt`. The model weights are not committed to this repository.
- **Microsoft ONNX Runtime**, MIT: <https://github.com/microsoft/onnxruntime>, Android version **1.24.3** in the experimental AI APK. The builder pins the AAR SHA-256. Native libraries for both ARM ABIs and Java bindings are bundled, with `assets/plantbrush/ONNXRUNTIME-LICENSE.txt` and attribution. The regular APK does not include this inference runtime.
- **MaLiang recognizer revision-3 reference data**, supplied with the original Windows recognizer: the Android experiment converts its reference index and catalog and independently ports the scoring behavior. Original reference data and game artwork retain their provenance; no new license or ownership is asserted. The Windows executable and Spanish companion-app code are not included. See [the implementation record](docs/magic-plantbrush-prototype.md).

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
