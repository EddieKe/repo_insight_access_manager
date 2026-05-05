# Azure DevOps Dashboard - Frontend

The frontend component of the Azure DevOps Repository Dashboard provides a modern, responsive user interface for interacting with Azure DevOps data. Built with React and Material UI, it offers an intuitive way to explore projects, repositories, security groups, and permissions.

## Architecture

The frontend is built with:

- **React**: Core UI library
- **Material UI**: Component library for consistent design
- **Vite**: Fast build tool and development server
- **Axios**: HTTP client for API communication

## Key Components

### Main Dashboard (`AzureDevopsDashboard.jsx`)

The primary component that orchestrates the entire UI. It handles:

- Authentication and configuration
- Project and repository selection
- Tab navigation
- Theme management (light/dark mode)
- Error handling and notifications

### API Integration (`azureAPI.js`)

Centralizes all API calls to the backend, including:

- Fetching projects, repositories, and groups
- Managing user and group permissions
- Configuration handling
- Cache management

## Features

### Project and Repository Management

- Browse all projects in your Azure DevOps organization
- View repositories within each project
- See repository details including default branch

### Security and Permissions

- Explore security groups and their members
- View detailed permissions for users and groups
- Analyze repository-specific permissions

### User Interface

- Responsive design for desktop and mobile
- Dark/light theme support
- Notifications for operation status
- Loading indicators for async operations

### Data Export

- Export permissions data to Excel
- Download repository member lists

## Development

### Prerequisites

- Node.js 16 or higher
- npm or yarn

### Setup

1. Install dependencies:
   ```
   npm install
   ```

2. Start the development server:
   ```
   npm run dev
   ```

3. Build for production:
   ```
   npm run build
   ```

### Environment Configuration

The frontend expects the backend API to be available at `http://localhost:5000/api` by default. You can modify this in the `azureAPI.js` file if your backend is hosted elsewhere.

## Component Structure

```
src/
├── api/
│   └── azureAPI.js        # API integration layer
├── components/
│   └── AzureDevopsDashboard.jsx  # Main application component
├── assets/                # Static assets
├── App.jsx                # Application entry point
└── main.jsx               # React mounting point
```

## State Management

The application uses React's useState and useEffect hooks for state management, with the following key states:

- Projects, repositories, and groups data
- User selections and preferences
- UI state (loading, errors, notifications)
- Theme configuration

## Styling

Material UI's theming system is used for consistent styling, with support for both light and dark modes. The theme is defined in the `AzureDevopsDashboard.jsx` file.