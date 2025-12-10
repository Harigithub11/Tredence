# Frontend Dashboard - Quick Start Guide

## 🚀 Quick Start (Windows)

### Option 1: Automated Setup (Recommended)

```bash
# Navigate to frontend directory
cd C:\Hari\JOB\Tredence\agent-workflow-engine\frontend

# Run the setup script
setup-and-run.bat
```

This will:
1. Install all dependencies
2. Check if backend is running
3. Start the development server
4. Open http://localhost:3000 in your browser

### Option 2: Manual Setup

```bash
# 1. Navigate to frontend directory
cd C:\Hari\JOB\Tredence\agent-workflow-engine\frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

Then open your browser to: **http://localhost:3000**

---

## 📋 Prerequisites

### 1. Node.js and npm

Check if installed:
```bash
node --version  # Should be v18 or higher
npm --version   # Should be v9 or higher
```

If not installed, download from: https://nodejs.org/

### 2. Backend API Running

The dashboard needs the backend API running on port 8001.

**Start the backend:**
```bash
cd C:\Hari\JOB\Tredence\agent-workflow-engine
docker-compose up -d
```

**Verify backend is running:**
```bash
curl http://localhost:8001/health
```

You should see:
```json
{
  "status": "healthy",
  "database": true,
  "timestamp": "..."
}
```

---

## 🎯 Testing the Dashboard

### 1. View the Dashboard

Open http://localhost:3000 in your browser

You should see:
- Header with "Workflow Engine" logo
- Navigation tabs (Dashboard / Code Review)
- Statistics cards (Total Runs, Running, Completed, Failed)
- Active Runs section
- System Health monitor

### 2. Test Code Review

1. Click on "Code Review" tab in the header
2. You'll see example code pre-filled
3. Configure options:
   - Quality Threshold: 70 (default)
   - Enable AI-powered suggestions: ✓ (if you have GEMINI_API_KEY)
4. Click "Run Code Review"
5. Watch the analysis happen in real-time
6. See results displayed below

### 3. Monitor Real-Time Updates

1. Submit a code review (as above)
2. Switch to "Dashboard" tab
3. Watch the active run appear with:
   - Progress bar (animated)
   - Current status
   - Time elapsed
   - Quality score (when complete)

### 4. Check WebSocket Connection

Look at the top-right corner:
- 🟢 Green dot = Connected
- Status text should say "Connected"

If disconnected:
- Check backend is running
- Check browser console for errors
- Verify WebSocket endpoint: ws://localhost:8001

---

## 🎨 Dashboard Features to Test

### Statistics Cards (Top)
- **Total Runs**: Shows all workflow executions
- **Running**: Currently executing workflows
- **Completed**: Successfully finished workflows
- **Failed**: Failed workflow executions

### Active Runs (Left Column)
Click on any active run to expand and see:
- Execution details
- Iterations count
- Execution time
- Recent events
- Error messages (if any)

### System Health (Right Column)
Shows real-time status of:
- ✅ API (should be green checkmark)
- ✅ Database (should be green checkmark)
- Last checked timestamp

### Workflow Stats (Right Column)
Displays:
- Average execution time
- Success rate
- Average quality score
- Trend indicators

---

## 🐛 Troubleshooting

### Issue: "npm: command not found"

**Solution**: Install Node.js from https://nodejs.org/

### Issue: Port 3000 already in use

**Solution**: Kill the process or use a different port:
```bash
# Use different port
npm run dev -- --port 3001
```

### Issue: Backend API not connecting

**Solution**:
1. Make sure backend is running:
   ```bash
   cd C:\Hari\JOB\Tredence\agent-workflow-engine
   docker-compose up -d
   ```

2. Check backend health:
   ```bash
   curl http://localhost:8001/health
   ```

3. If backend is down:
   ```bash
   docker-compose logs app
   ```

### Issue: WebSocket not connecting

**Solution**:
1. Open browser Developer Tools (F12)
2. Go to Console tab
3. Look for WebSocket errors
4. Check Network tab for WS connections
5. Verify backend WebSocket endpoint is accessible

### Issue: Blank page or errors

**Solution**:
1. Clear browser cache (Ctrl + Shift + Delete)
2. Check browser console for errors (F12)
3. Restart development server:
   ```bash
   # Press Ctrl+C to stop
   npm run dev
   ```

### Issue: Dependencies installation fails

**Solution**:
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules
rmdir /s /q node_modules

# Reinstall
npm install
```

---

## 📱 Browser Support

Tested and working on:
- ✅ Chrome (latest)
- ✅ Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)

---

## 🔧 Development Commands

```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint

# Type check
npm run type-check

# Format code
npm run format
```

---

## 📊 What to Expect

### On First Load
- Dashboard with empty state
- "No active workflow runs" message
- System health showing green status
- Statistics showing zeros

### After Running Code Review
- Active run appears in dashboard
- Progress bar animates
- Status updates in real-time
- Quality score appears when complete
- Results shown in Recent Analysis

### Real-Time Updates
- WebSocket connection established
- Progress bar updates live
- Status changes reflected immediately
- Completion notifications

---

## 🎯 Next Steps

1. **Test the dashboard** - Submit a code review and watch it execute
2. **Explore the UI** - Click around and check all features
3. **Monitor WebSocket** - Open browser DevTools and watch Network tab
4. **Check real-time updates** - Run multiple reviews and watch them update
5. **Customize** - Modify components in `src/components/` to customize

---

## 📞 Need Help?

If you encounter issues:

1. Check this troubleshooting section
2. Look at browser console (F12)
3. Check backend logs: `docker-compose logs -f app`
4. Verify all services are running: `docker-compose ps`

---

## 🎉 Success!

If you see the dashboard with:
- ✅ Green "Connected" status
- ✅ System Health showing green checkmarks
- ✅ Able to submit code review
- ✅ Real-time progress updates

**Congratulations! Your dashboard is working perfectly!** 🎊

---

**Built with React + TypeScript + TailwindCSS**
