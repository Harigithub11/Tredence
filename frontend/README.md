# Workflow Orchestration Dashboard

React + TypeScript frontend for real-time workflow monitoring and execution.

## Features

- ✅ Real-time workflow execution monitoring via WebSocket
- ✅ Progress visualization with animated progress bars
- ✅ Code review interface with syntax highlighting
- ✅ Complexity analysis charts with Chart.js
- ✅ System health monitoring
- ✅ Responsive design with TailwindCSS
- ✅ TypeScript for type safety

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Chart.js** - Data visualization
- **Axios** - HTTP client
- **WebSocket** - Real-time updates
- **Lucide React** - Icons
- **date-fns** - Date formatting

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Or with yarn
yarn install
```

### Development

```bash
# Start development server
npm run dev

# Open http://localhost:3000
```

### Build for Production

```bash
# Type check
npm run type-check

# Build
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── Dashboard.tsx    # Main dashboard
│   │   ├── ActiveRuns.tsx   # Active workflow runs
│   │   ├── RecentAnalysis.tsx
│   │   ├── SystemHealth.tsx
│   │   ├── WorkflowStats.tsx
│   │   ├── CodeReviewForm.tsx
│   │   └── Header.tsx
│   ├── hooks/              # Custom React hooks
│   │   └── useWebSocket.ts # WebSocket connection hook
│   ├── services/           # API clients
│   │   └── api.ts          # Backend API client
│   ├── types/              # TypeScript types
│   │   └── index.ts        # Type definitions
│   ├── App.tsx             # Root component
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── public/                 # Static assets
├── index.html              # HTML template
├── package.json            # Dependencies
├── tsconfig.json           # TypeScript config
├── vite.config.ts          # Vite config
└── tailwind.config.js      # Tailwind config
```

## Components

### Dashboard
Main dashboard view with:
- Workflow statistics cards
- Active runs monitoring
- Recent analysis results
- System health status

### ActiveRuns
Real-time monitoring of active workflow executions:
- Progress bars with percentage
- Current node execution status
- Time elapsed
- Quality scores
- WebSocket live updates

### CodeReviewForm
Interface for submitting code for review:
- Code editor with syntax highlighting
- Configuration options (LLM enabled, quality threshold)
- Real-time analysis results
- Complexity visualization

### RecentAnalysis
Display recent code review results:
- Quality scores
- Issue counts
- Complexity metrics
- Time/Space complexity charts

## WebSocket Integration

The dashboard uses WebSocket for real-time updates:

```typescript
// Connect to workflow run
const { isConnected, messages } = useWebSocket(runId)

// Messages received:
// - status_update: Workflow status changes
// - node_completed: Node execution completed
// - workflow_completed: Workflow finished
// - progress_update: Progress percentage
// - log: Execution logs
```

## API Integration

Backend API endpoints used:

```typescript
// Health check
GET /health

// Graph operations
GET /graph/{id}
GET /graph/name/{name}
POST /graph/create
DELETE /graph/{id}

// Workflow execution
POST /graph/run
GET /graph/state/{run_id}

// WebSocket
WS /ws/run/{run_id}
```

## Environment Variables

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Styling

TailwindCSS utility classes with custom components:

```css
/* Custom classes */
.card        - Card container
.btn         - Button base
.btn-primary - Primary button
.input       - Form input
.badge       - Status badge
```

## Type Safety

Full TypeScript coverage:
- API response types
- WebSocket message types
- Component prop types
- Hook return types

## Development Tips

### Hot Module Replacement
Vite provides instant HMR for fast development.

### Linting
```bash
npm run lint
```

### Formatting
```bash
npm run format
```

### Type Checking
```bash
npm run type-check
```

## Docker Deployment

### Build Docker Image

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Add to docker-compose.yml

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  container_name: workflow_frontend
  ports:
    - "3000:80"
  depends_on:
    - api
  networks:
    - workflow_network
```

## Features Roadmap

### Implemented ✅
- [x] Real-time WebSocket updates
- [x] Progress visualization
- [x] Code review interface
- [x] System health monitoring
- [x] Responsive design

### Planned 🚧
- [ ] User authentication
- [ ] Workflow template library
- [ ] Visual DAG editor
- [ ] Advanced filtering
- [ ] Export reports
- [ ] Dark mode
- [ ] Workflow history timeline
- [ ] Performance analytics

## Troubleshooting

### WebSocket Connection Failed
- Check backend is running on port 8000
- Verify WebSocket endpoint is accessible
- Check browser console for errors

### API Calls Failing
- Ensure CORS is enabled on backend
- Verify API_URL environment variable
- Check network tab in browser DevTools

### Build Errors
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear cache: `rm -rf .vite`
- Update dependencies: `npm update`

## Contributing

1. Create feature branch
2. Make changes
3. Run tests and type check
4. Submit pull request

## License

Part of the Agent Workflow Engine project.

---

**Built with ❤️ using React + TypeScript + TailwindCSS**
