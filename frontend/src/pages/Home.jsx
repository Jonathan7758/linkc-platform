import { useState, useEffect } from "react"
import { robotsApi, tasksApi, agentsApi, spacesApi } from "../services/api"

function Home() {
  const [robots, setRobots] = useState([])
  const [tasks, setTasks] = useState([])
  const [agents, setAgents] = useState([])
  const [buildings, setBuildings] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState("dashboard")

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [robotsRes, tasksRes, agentsRes, buildingsRes] = await Promise.all([
        robotsApi.list(),
        tasksApi.list(),
        agentsApi.list(),
        spacesApi.listBuildings()
      ])
      setRobots(robotsRes.data.robots || [])
      setTasks(tasksRes.data.tasks || [])
      setAgents(agentsRes.data.agents || [])
      setBuildings(buildingsRes.data.buildings || [])
    } catch (error) {
      console.error("Failed to fetch data:", error)
    } finally {
      setLoading(false)
    }
  }

  const runAgent = async (agentId) => {
    try {
      const res = await agentsApi.run(agentId)
      alert(res.data.message || "Agent 执行完成")
      fetchData()
    } catch (error) {
      alert("执行失败: " + (error.response?.data?.detail || error.message))
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      idle: "#4caf50", working: "#2196f3", charging: "#ff9800",
      error: "#f44336", offline: "#9e9e9e", pending: "#ff9800",
      in_progress: "#2196f3", completed: "#4caf50", assigned: "#9c27b0"
    }
    return colors[status] || "#9e9e9e"
  }

  if (loading) return <div className="container"><p>加载中...</p></div>

  return (
    <div className="container">
      <header className="header">
        <h1>LinkC Platform</h1>
        <p className="subtitle">物业机器人协同平台</p>
      </header>

      <nav className="tabs">
        {["dashboard", "robots", "tasks", "agents"].map(tab => (
          <button key={tab} className={"tab " + (activeTab === tab ? "active" : "")}
            onClick={() => setActiveTab(tab)}>
            {tab === "dashboard" ? "仪表盘" : tab === "robots" ? "机器人" : tab === "tasks" ? "任务" : "Agent"}
          </button>
        ))}
      </nav>

      {activeTab === "dashboard" && (
        <div className="stats-grid">
          <div className="stat-card"><h3>{robots.length}</h3><p>机器人总数</p></div>
          <div className="stat-card"><h3>{robots.filter(r => r.status === "working").length}</h3><p>工作中</p></div>
          <div className="stat-card"><h3>{tasks.filter(t => t.status === "pending").length}</h3><p>待分配任务</p></div>
          <div className="stat-card"><h3>{buildings.length}</h3><p>管理楼宇</p></div>
        </div>
      )}

      {activeTab === "robots" && (
        <div>
          <h2>机器人列表 <button className="refresh-btn" onClick={fetchData}>刷新</button></h2>
          <div className="cards-grid">
            {robots.map(robot => (
              <div key={robot.id} className="card">
                <div className="card-header">
                  <span>{robot.name}</span>
                  <span className="status-badge" style={{backgroundColor: getStatusColor(robot.status)}}>{robot.status}</span>
                </div>
                <div className="card-body">
                  <p><strong>品牌:</strong> {robot.brand}</p>
                  <p><strong>电量:</strong> {robot.battery_level}%</p>
                  <div className="battery-bar"><div className="battery-fill" style={{width: robot.battery_level + "%", backgroundColor: robot.battery_level > 20 ? "#4caf50" : "#f44336"}} /></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "tasks" && (
        <div>
          <h2>任务列表 <button className="refresh-btn" onClick={fetchData}>刷新</button></h2>
          <div className="cards-grid">
            {tasks.map(task => (
              <div key={task.id} className="card">
                <div className="card-header">
                  <span>{task.name}</span>
                  <span className="status-badge" style={{backgroundColor: getStatusColor(task.status)}}>{task.status}</span>
                </div>
                <div className="card-body">
                  <p><strong>优先级:</strong> {task.priority}</p>
                  <p><strong>机器人:</strong> {task.robot_id || "未分配"}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "agents" && (
        <div>
          <h2>Agent 列表</h2>
          <div className="cards-grid">
            {agents.map(agent => (
              <div key={agent.agent_id} className="card">
                <div className="card-header">
                  <span>{agent.name}</span>
                  <span className="status-badge" style={{backgroundColor: getStatusColor(agent.state)}}>{agent.state}</span>
                </div>
                <div className="card-body">
                  <p><strong>自主级别:</strong> {agent.autonomy_level}</p>
                  <button className="action-btn" onClick={() => runAgent(agent.agent_id)}>运行 Agent</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Home
