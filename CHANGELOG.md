# CHANGELOG


## v0.7.0 (2026-08-24)

### Bug Fixes

- Fail clearly when a deployment has no virtual environment
  ([`2010bbb`](https://github.com/bec-project/bec_launcher/commit/2010bbba75ad765f5731b91f40d4615318ac86dd))

### Build System

- Require PySide6 6.11.1 to match bec_widgets
  ([`9662392`](https://github.com/bec-project/bec_launcher/commit/9662392172ceaf5628326ee092165b34ec465aea))

### Documentation

- Document the Linux default of --pycache-prefix
  ([`f300c64`](https://github.com/bec-project/bec_launcher/commit/f300c649f86d8dcf6c7c3e27caec537943dfd1c4))

### Features

- Fall back to the legacy launch flow for deployments without progress support
  ([`eeb9c03`](https://github.com/bec-project/bec_launcher/commit/eeb9c03a6a86fecea4b8705bcfb3038382429da4))

- Show cache warm-up indicator at the bottom of the launcher
  ([`01ea1bf`](https://github.com/bec-project/bec_launcher/commit/01ea1bf2e4b0bee16b0cfc56eb6ab0e9b65be83c))

- Stream GUI startup progress into an animated loading banner
  ([`e91b1db`](https://github.com/bec-project/bec_launcher/commit/e91b1dbecb9853ccf2a7c6135a7d0d8692d619aa))

- Support a configurable Python bytecode cache prefix
  ([`bf7c4bf`](https://github.com/bec-project/bec_launcher/commit/bf7c4bf20319d93e4fef339502c24cfd828c4800))

- Warm deployment Python caches in the background on startup
  ([`83491c5`](https://github.com/bec-project/bec_launcher/commit/83491c50ec446970675020981309d79b5823e547))

### Refactoring

- Drop the ineffective --demo flag from the banner preview
  ([`a6d61a4`](https://github.com/bec-project/bec_launcher/commit/a6d61a4a00766ac1b329939a2d536ac224f47891))


## v0.6.1 (2026-07-02)

### Bug Fixes

- Ensure PYTHONPYCACHEPREFIX is set correctly in deployment launch command
  ([`0dca56d`](https://github.com/bec-project/bec_launcher/commit/0dca56dd5affe4f1baf3bdf17a06791ae2517eeb))

- Update BEC_LAUNCHER_BRANCH fallback to use github.head_ref or github.sha
  ([`97c2a1b`](https://github.com/bec-project/bec_launcher/commit/97c2a1b1217c2fb6ef7afd76b24212244235157a))


## v0.6.0 (2026-07-02)

### Features

- Add PYTHONPYCACHEPREFIX support for Linux deployments
  ([`ef0b883`](https://github.com/bec-project/bec_launcher/commit/ef0b8831a6d08c1c3d9a9573e95e9435f1946ab8))


## v0.5.1 (2026-03-30)

### Bug Fixes

- Default deployment selection if single deployment
  ([`645cd5e`](https://github.com/bec-project/bec_launcher/commit/645cd5ebb7519c40147b7a7480b864cfcea1e9e4))


## v0.5.0 (2026-03-26)

### Bug Fixes

- **tooltip**: Styling in the same way as the rest of the app
  ([`b7d6724`](https://github.com/bec-project/bec_launcher/commit/b7d6724c34c5a934e294288e300397eab9177070))

### Features

- Add tooltip to default app selection
  ([`704e5cf`](https://github.com/bec-project/bec_launcher/commit/704e5cf7701d42c15fb0580f4742d3f99f6816d6))

- **defaults**: Defaults saving logic changed
  ([`9b81fcf`](https://github.com/bec-project/bec_launcher/commit/9b81fcfcbd8f5e6be34d7849c3e249fd7b87f3a1))


## v0.4.0 (2026-03-24)

### Features

- **gui**: Add option to launch commands in a new terminal window
  ([`e30d80b`](https://github.com/bec-project/bec_launcher/commit/e30d80b41e95ba9e76860639ae35395ec1adb4fc))


## v0.3.1 (2026-03-20)

### Bug Fixes

- **main**: Setapplicationname("bec")
  ([`892d915`](https://github.com/bec-project/bec_launcher/commit/892d91595228b7793b8de3d7f7b57dfb036ff855))


## v0.3.0 (2026-03-18)

### Bug Fixes

- **backend**: Default path to the bec deployments
  ([`3063b99`](https://github.com/bec-project/bec_launcher/commit/3063b99a3e2bbc58d699ebcf0bb24560d5c06c10))

### Build System

- **gui**: Added qt packages
  ([`346fd27`](https://github.com/bec-project/bec_launcher/commit/346fd2773fcdd2ec948aa77394bd0ad198e63cc3))

### Chores

- **git**: Gitignore QtDesignStudio files
  ([`e335bed`](https://github.com/bec-project/bec_launcher/commit/e335bed255158a8cf05a47955a3b3753efbc0575))

### Features

- **gui**: Qml based gui added
  ([`cd97b0c`](https://github.com/bec-project/bec_launcher/commit/cd97b0ccfb406e5c616c8671628e6d57cb0c3ac4))

- **script**: Added `launcher` script for cli
  ([`9bf8884`](https://github.com/bec-project/bec_launcher/commit/9bf888429d53b6da783e7ce8d9e919e62a026101))


## v0.2.0 (2026-01-12)

### Bug Fixes

- Correct repository reference in sync-issues-pr workflow
  ([`2f36cb8`](https://github.com/bec-project/bec_launcher/commit/2f36cb883c9ed0f83f72bea55465eccc6e3a425f))

### Features

- Add launch_deployment function for executing commands in new terminal
  ([`5d1c82d`](https://github.com/bec-project/bec_launcher/commit/5d1c82dc09be01197a7ccca5c7a80c72ab6f3437))

### Testing

- Add tests for launch_deployment function across macOS and Linux platforms
  ([`63e61fe`](https://github.com/bec-project/bec_launcher/commit/63e61fe54bd15be334bc6fc5a3b951f749b69a1e))


## v0.1.0 (2026-01-09)

### Features

- Simple launch file to demonstrate usage
  ([`4ee8761`](https://github.com/bec-project/bec_launcher/commit/4ee87619a2dad87a8cd6bd2a28bc3f8b7b05af14))

### Refactoring

- Enhance type safety by introducing DeploymentDict for deployment names
  ([`47e47da`](https://github.com/bec-project/bec_launcher/commit/47e47dac3cf3aaab5084bc4e32fbd194bf55f54d))
