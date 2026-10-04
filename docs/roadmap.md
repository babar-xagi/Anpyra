# Roadmap

Version 0.1 establishes one installable framework around the demonstrated native compiler. This roadmap lists future work; the listed features are not currently implemented.

1. **Device acceptance and compiler contracts.** Run hello and score on the Android devices used for the experiments; add an independent DEX/APK verifier to release checks; record device/API results; expand diagnostics and bytecode regression cases.
2. **Language semantics.** Add assignments/reassignments, register lifetime analysis, larger constants, compound expressions, helper-local statements and control flow, and helpers calling helpers. Specify integer overflow and object lifetimes before extending syntax.
3. **Application UI.** Introduce layouts and more native widgets, then event callbacks/listeners and persistent state. Keep widgets and lifecycle bindings separate from compiler lowering.
4. **Project structure.** Support multiple Python modules, imports between compiled modules, assets/resources, and more than one Activity. Add a linker/module model rather than executing host imports.
5. **Release workflows.** Add explicit release signing material, protected-key handling, package/version upgrade checks, and documented device compatibility. Evaluate v3 signing, resources, AAB output, and publishing only after those contracts exist.

The next milestone should be a small interactive application that exercises a layout, a button callback, typed state, and text updates on a real phone. Keep the existing examples working at each step.
