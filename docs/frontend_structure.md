# Frontend Structure (`web/`)

This document outlines the structure of the frontend application located in the `web/` directory. The frontend is built using Next.js and React with TypeScript.

## Root Directory (`web/`)

The root `web/` directory contains project configuration files and top-level directories:

*   **`.next/`**: Output directory for the Next.js build.
*   **`node_modules/`**: Contains all project dependencies.
*   **`public/`**: Static assets that are publicly accessible.
    *   `images/`: Image files.
    *   `mock/`: Mock data for development or testing.
    *   `replay/`: Assets related to replay functionality.
*   **`src/`**: The main application source code.
*   **Configuration Files**:
    *   `next-env.d.ts`: TypeScript declaration file for Next.js environment variables.
    *   `tsconfig.json`: TypeScript compiler options.
    *   `prettier.config.js`: Prettier code formatter configuration.
    *   `postcss.config.js`: PostCSS (CSS preprocessor) configuration.
    *   `pnpm-lock.yaml`: PNPM lock file for dependency management.
    *   `package.json`: Project metadata, scripts, and dependencies.
    *   `next.config.js`: Next.js framework configuration.
    *   `eslint.config.js`: ESLint configuration for code linting.
    *   `docker-compose.yml`: Docker Compose configuration for containerization.
    *   `components.json`: Likely related to UI component management or theming (e.g., shadcn/ui).
    *   `Dockerfile`: Instructions for building a Docker image for the frontend.
    *   `README.md`: Frontend-specific README.
    *   `.npmrc`: PNPM configuration file.
    *   `.gitignore`: Specifies intentionally untracked files that Git should ignore.
    *   `.dockerignore`: Specifies files to ignore when building the Docker image.

## Source Directory (`web/src/`)

The `web/src/` directory is the heart of the frontend application.

*   **`app/`**: Contains the application's routes and pages, following the Next.js App Router conventions.
    *   **`chat/`**: Contains the components and logic for the main chat interface, including CppCheck input capabilities.
        *   **`components/`**: Chat-specific components including:
            *   `input-box.tsx`: Enhanced input component with dual mode support (text and CppCheck)
            *   `messages-block.tsx`: Main chat container with CppCheck analysis integration
            *   `message-list-view.tsx`: Message display components
            *   `welcome.tsx`: Welcome screen
            *   `conversation-starter.tsx`: Quick-start suggestions
    *   **`landing/`**: Components for the application's landing page.
    *   **`settings/`**: Components for application settings or user preferences.
    *   `page.tsx`: The main entry point or a primary page for the application (could be a redirect or a simple layout).
    *   `layout.tsx`: Defines the root layout for the application, often including common UI elements like headers and footers.
*   **`components/`**: Reusable UI components.
    *   **`deer-flow/`**: Components specific to the "Deer Flow" branding or core application features.
    *   **`editor/`**: Components related to a code editor or rich text input.
    *   **`magicui/`**: Potentially a collection of advanced or animated UI components.
    *   **`ui/`**: General-purpose UI components, possibly from a library like shadcn/ui.
    *   `theme-provider.tsx`: A component for managing application themes (e.g., light/dark mode).
*   **`core/`**: Core logic, services, and utilities.
    *   **`api/`**: Functions for making API calls to the backend.
        *   `chat.ts`: Enhanced with `cppCheckAnalysisStream()` for CppCheck-specific API calls
        *   `types.ts`: Type definitions including `CppCheckData` interface
    *   **`mcp/`**: Code related to Multi-Server Client Protocol (MCP) interactions.
    *   **`messages/`**: Utilities and types related to message handling in the chat interface.
        *   `types.ts`: Message types including `CppCheckData` interface
        *   `index.ts`: Exports for message-related types and functions
    *   **`rehype/`**: Configuration or plugins for Rehype (HTML processor, often used with Markdown).
    *   **`replay/`**: Logic for replaying or displaying past interactions.
    *   **`sse/`**: Server-Sent Events handling for real-time communication.
    *   **`store/`**: State management logic (e.g., using Zustand, Redux, or React Context).
        *   `store.ts`: Enhanced with `sendCppCheckAnalysis()` function for CppCheck workflow
    *   **`utils/`**: General utility functions.
*   **`hooks/`**: Custom React hooks for reusable component logic.
*   **`lib/`**: Library code, helper functions, and third-party integrations.
*   **`styles/`**: Global styles, CSS modules, or styling-related configurations.
*   **`typings/`**: TypeScript declaration files for modules that don't have their own types.
*   `env.js`: Potentially for managing environment variables on the client-side.

## CppCheck Integration Features

The frontend provides a comprehensive interface for CppCheck defect analysis:

*   **Dual Input Mode**: The main input box supports switching between:
    *   **Text Mode**: Traditional chat input for general queries
    *   **CppCheck Mode**: Structured form for defect analysis with fields:
        *   File path (with file icon)
        *   Line number (numeric input with hash icon)
        *   Severity (dropdown: error, warning, style, performance, information)
        *   Defect ID (text input with message icon)
        *   Summary (text input with file icon)

*   **API Integration**: 
    *   Dedicated streaming endpoint (`/api/cppcheck/analyze`)
    *   Real-time analysis results with proper error handling
    *   Automatic message formatting for display

*   **User Experience**:
    *   Smooth mode switching with animation
    *   Clear visual indicators for current input mode
    *   Form validation and user feedback
    *   Consistent styling with the rest of the application

*   **Type Safety**: 
    *   Comprehensive TypeScript interfaces for CppCheck data
    *   Proper typing throughout the component hierarchy
    *   Type-safe API calls and state management

## Key Technologies and Patterns

*   **Next.js**: React framework for server-side rendering, static site generation, and routing.
*   **React**: JavaScript library for building user interfaces.
*   **TypeScript**: Superset of JavaScript that adds static typing.
*   **Tailwind CSS / PostCSS**: Likely used for styling, based on `postcss.config.js`.
*   **shadcn/ui / `components.json`**: Suggests the use of shadcn/ui for pre-built, customizable UI components.
*   **ESLint / Prettier**: For code linting and formatting.
*   **Docker**: For containerization and deployment.
*   **PNPM**: Package manager.
*   **App Router**: The `web/src/app/` directory structure indicates use of the Next.js App Router for routing.
*   **Framer Motion**: For smooth animations in the input mode transitions.
*   **Lucide React**: For consistent iconography throughout the interface. 