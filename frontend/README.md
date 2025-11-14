# Smart Inventory System - Frontend

React + TypeScript + Vite frontend application for the Smart Inventory System.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS v4** - Styling
- **React Query (@tanstack/react-query)** - Server state management
- **Zustand** - Client state management
- **React Router** - Routing
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **React ZXing** - Barcode scanning
- **React Hot Toast** - Notifications

## Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/          # Page components
├── services/       # API services
├── hooks/          # Custom React hooks
├── store/          # Zustand stores
├── types/          # TypeScript type definitions
├── utils/          # Utility functions
└── assets/         # Static assets
```

## Getting Started

### Prerequisites

- Node.js 20.19+ or 22.12+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Features

- Authentication with JWT tokens
- Responsive design with Tailwind CSS
- Real-time notifications
- Barcode scanning capability
- Data visualization with charts
- Optimistic UI updates
- Error handling and retry logic

## API Integration

The application connects to the backend API at the URL specified in `VITE_API_BASE_URL`. All API calls include:

- Automatic token injection
- Error handling with user-friendly messages
- Request/response interceptors
- Automatic token refresh on 401 errors
