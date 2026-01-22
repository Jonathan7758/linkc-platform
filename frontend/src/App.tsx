import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';
import { TrainerWorkbench } from './pages/TrainerWorkbench';
import { OperationsDashboard } from './pages/OperationsDashboard';
import { TaskManagement } from './pages/TaskManagement';
import { RobotMonitoring } from './pages/RobotMonitoring';
import { AlertManagement } from './pages/AlertManagement';
import { ExecutiveOverview } from './pages/ExecutiveOverview';
import { AnalyticsDashboard } from './pages/AnalyticsDashboard';
import { ReportCenter } from './pages/ReportCenter';
import { MobileMonitor } from './pages/MobileMonitor';
import { MobileTask } from './pages/MobileTask';
import { MobileAlert } from './pages/MobileAlert';

// DM3 & DM5: Demo Components
import { DemoControlPanel, DemoModeIndicator } from './components/demo';
import DemoMapPage from './pages/DemoMapPage';

// Navigation component for demo purposes
const Navigation: React.FC = () => {
  return (
    <nav className="bg-gray-800 text-white p-4">
      <div className="container mx-auto flex items-center justify-between">
        <Link to="/executive" className="text-xl font-bold hover:text-blue-300">LinkC Platform</Link>
        <div className="flex space-x-4">
          {/* Executive Dashboard */}
          <div className="relative group">
            <span className="cursor-pointer hover:text-blue-300">战略驾驶舱 ▼</span>
            <div className="absolute left-0 mt-2 w-40 bg-white rounded shadow-lg hidden group-hover:block z-10">
              <Link to="/executive" className="block px-4 py-2 text-gray-800 hover:bg-gray-100">总览</Link>
              <Link to="/analytics" className="block px-4 py-2 text-gray-800 hover:bg-gray-100">数据分析</Link>
              <Link to="/reports" className="block px-4 py-2 text-gray-800 hover:bg-gray-100">报表中心</Link>
            </div>
          </div>
          {/* Operations Console */}
          <div className="relative group">
            <span className="cursor-pointer hover:text-blue-300">运营控制台 ▼</span>
            <div className="absolute left-0 mt-2 w-40 bg-white rounded shadow-lg hidden group-hover:block z-10">
              <Link to="/operations" className="block px-4 py-2 text-gray-800 hover:bg-gray-100">运营总览</Link>
              <Link to="/tasks" className="block px-4 py-2 text-gray-800 hover:bg-gray-100">任务管理</Link>
              <Link to="/robots" className="block px-4 py-2 text-gray-800 hover:bg-gray-100">机器人监控</Link>
              <Link to="/alerts" className="block px-4 py-2 text-gray-800 hover:bg-gray-100">告警管理</Link>
            </div>
          </div>
          {/* Training Workbench */}
          <Link to="/trainer" className="hover:text-blue-300">训练工作台</Link>
          {/* Demo Map */}
          <Link to="/demo/map" className="hover:text-blue-300">实时地图</Link>
        </div>
      </div>
    </nav>
  );
};

// Layout wrapper with navigation
const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navigation />
      <main>{children}</main>
    </div>
  );
};

const App: React.FC = () => {
  // Demo control panel visibility state
  const [showDemoPanel, setShowDemoPanel] = useState(false);

  // Default tenant and building IDs for demo
  const tenantId = 'demo_tenant_001';
  const buildingId = 'building_001';

  // Navigation handlers
  const handleNavigateToAlerts = () => { window.location.href = '/alerts'; };
  const handleNavigateToTasks = () => { window.location.href = '/tasks'; };
  const handleNavigateToRobots = () => { window.location.href = '/robots'; };
  const handleNavigateToOperations = () => { window.location.href = '/operations'; };
  const handleNavigateToAnalytics = () => { window.location.href = '/analytics'; };
  const handleNavigateToReports = () => { window.location.href = '/reports'; };

  return (
    <BrowserRouter>
      {/* DM3: Demo Mode Indicator - Shows at top when demo is active */}
      <DemoModeIndicator onClick={() => setShowDemoPanel(true)} />

      {/* DM3: Demo Control Panel - Floating panel for demo control */}
      <DemoControlPanel
        visible={showDemoPanel}
        onClose={() => setShowDemoPanel(false)}
        position="bottom-right"
      />

      <Routes>
        {/* Executive Dashboard Routes (E1-E3) */}
        <Route
          path="/executive"
          element={
            <Layout>
              <ExecutiveOverview
                tenantId={tenantId}
                onNavigateToOperations={handleNavigateToOperations}
                onNavigateToAnalytics={handleNavigateToAnalytics}
                onNavigateToReports={handleNavigateToReports}
              />
            </Layout>
          }
        />
        <Route
          path="/analytics"
          element={
            <Layout>
              <AnalyticsDashboard tenantId={tenantId} />
            </Layout>
          }
        />
        <Route
          path="/reports"
          element={
            <Layout>
              <ReportCenter tenantId={tenantId} />
            </Layout>
          }
        />

        {/* Operations Dashboard Routes (O1-O4) */}
        <Route
          path="/operations"
          element={
            <Layout>
              <OperationsDashboard
                tenantId={tenantId}
                onNavigateToAlerts={handleNavigateToAlerts}
                onNavigateToTasks={handleNavigateToTasks}
                onNavigateToRobots={handleNavigateToRobots}
              />
            </Layout>
          }
        />
        <Route
          path="/tasks"
          element={
            <Layout>
              <TaskManagement
                tenantId={tenantId}
                onTaskClick={(taskId) => console.log('Task clicked:', taskId)}
              />
            </Layout>
          }
        />
        <Route
          path="/robots"
          element={
            <Layout>
              <RobotMonitoring
                tenantId={tenantId}
                buildingId={buildingId}
                onRobotSelect={(robotId) => console.log('Robot selected:', robotId)}
              />
            </Layout>
          }
        />
        <Route
          path="/alerts"
          element={
            <Layout>
              <AlertManagement
                tenantId={tenantId}
                onAlertClick={(alertId) => console.log('Alert clicked:', alertId)}
              />
            </Layout>
          }
        />

        {/* Training Workbench Route (T1-T4) */}
        <Route
          path="/trainer"
          element={
            <Layout>
              <TrainerWorkbench
                tenantId={tenantId}
                buildingId={buildingId}
              />
            </Layout>
          }
        />

        {/* DM5: Demo Map Visualization Route */}
        <Route
          path="/demo/map"
          element={<DemoMapPage />}
        />

        {/* Mobile Routes (P1-P3) */}
        <Route
          path="/mobile"
          element={
            <MobileMonitor
              tenantId={tenantId}
              onRobotSelect={(robotId) => console.log('Robot selected:', robotId)}
              onAlertSelect={() => { window.location.href = '/mobile/alerts'; }}
            />
          }
        />
        <Route
          path="/mobile/tasks"
          element={
            <MobileTask
              tenantId={tenantId}
              onBack={() => { window.location.href = '/mobile'; }}
            />
          }
        />
        <Route
          path="/mobile/alerts"
          element={
            <MobileAlert
              tenantId={tenantId}
              onBack={() => { window.location.href = '/mobile'; }}
              onRobotSelect={(robotId) => console.log('Robot selected:', robotId)}
              onTaskSelect={() => { window.location.href = '/mobile/tasks'; }}
            />
          }
        />

        {/* Default redirect to executive dashboard */}
        <Route path="/" element={<Navigate to="/executive" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
