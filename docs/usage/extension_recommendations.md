# IDE Extensions for SWE-agent

SWE-agent can be integrated directly into your development workflow through IDE extensions. This page provides information about available extensions and how to use them.

## Available Extensions

- [VS Code Extension](#vs-code-extension) - Extension for Visual Studio Code
- [JetBrains Plugin](#jetbrains-plugin) - Plugin for IntelliJ IDEA and other JetBrains IDEs

## VS Code Extension

The VS Code extension provides seamless integration between SWE-agent and your Visual Studio Code workflow.

### Installation

1. Download the VSIX file from the [releases](https://github.com/SWE-agent/SWE-agent/releases) page
2. Open VS Code
3. Go to Extensions view (Ctrl+Shift+X)
4. Click "..." and select "Install from VSIX..."
5. Select the downloaded VSIX file

### Configuration

1. Open settings (Ctrl+,)
2. Search for "SWE-agent"
3. Configure the following settings:
   - `sweAgent.githubToken`: GitHub token for authentication
   - `sweAgent.apiKey`: API key for the language model
   - `sweAgent.modelProvider`: Language model provider (openai, anthropic, google, cohere)
   - `sweAgent.modelName`: Name of the language model to use
   - `sweAgent.sweAgentPath`: Path to SWE-agent installation

### Usage

The extension adds a SWE-agent sidebar to VS Code with access to the following features:

#### Fixing a GitHub Issue

1. Press Ctrl+Shift+P to open the Command Palette
2. Type "SWE-agent: Fix GitHub Issue"
3. Enter the GitHub issue URL when prompted
4. SWE-agent will work to solve the issue
5. Review the changes in the editor
6. Create a PR if desired

#### Creating a PR

1. Make your changes to the code
2. Right-click in the editor
3. Select "SWE-agent: Create PR for Fix"
4. Enter PR details when prompted
5. SWE-agent will create the PR on GitHub

#### Accessing the Dashboard

1. Press Ctrl+Shift+P to open the Command Palette
2. Type "SWE-agent: Open Dashboard"
3. The SWE-agent dashboard will open in your browser

## JetBrains Plugin

The JetBrains plugin integrates SWE-agent with IntelliJ IDEA and other JetBrains IDEs.

### Installation

1. Download the plugin JAR file from the [releases](https://github.com/SWE-agent/SWE-agent/releases) page
2. Open your JetBrains IDE
3. Go to Settings → Plugins
4. Click "Install Plugin from Disk..."
5. Select the downloaded JAR file
6. Restart the IDE when prompted

### Configuration

1. Go to Settings → Tools → SWE-agent
2. Configure the following settings:
   - GitHub token
   - API key for the language model
   - Model provider
   - Model name
   - Path to SWE-agent installation

### Usage

The plugin adds a SWE-agent tool window to your IDE with access to the following features:

#### Fixing a GitHub Issue

1. Open the SWE-agent tool window (View → Tool Windows → SWE-agent)
2. Click "Fix GitHub Issue"
3. Enter the GitHub issue URL when prompted
4. SWE-agent will work to solve the issue
5. Review the changes in the editor
6. Create a PR if desired

#### Creating a PR

1. Make your changes to the code
2. Go to SWE-agent → Create PR for Fix in the main menu
3. Enter PR details when prompted
4. SWE-agent will create the PR on GitHub

#### Accessing the Dashboard

1. Open the SWE-agent tool window
2. Click "Open Dashboard"
3. The SWE-agent dashboard will open in your browser

## Building from Source

If you prefer to build the extensions from source, you can find the source code in the [`ide_extensions`](https://github.com/SWE-agent/SWE-agent/tree/main/ide_extensions) directory of the SWE-agent repository.

### VS Code Extension

```bash
cd ide_extensions/vscode
npm install
npm run compile
```

### JetBrains Plugin

```bash
cd ide_extensions/jetbrains
./gradlew build
```

## Future Extensions

We are working on additional IDE integrations, including:

- Eclipse Plugin
- Visual Studio Integration
- GitHub Copilot-like inline suggestions

Stay tuned for updates!