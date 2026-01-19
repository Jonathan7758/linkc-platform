import { useState, useEffect } from "react"
import api from "../services/api"

function Home() {
  const [apiInfo, setApiInfo] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        const response = await api.get("/api/v1/info")
        setApiInfo(response.data)
      } catch (error) {
        console.error("Failed to fetch API info:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchInfo()
  }, [])

  return (
    <div className="container">
      <h1>LinkC Platform</h1>
      {loading ? (
        <p>Loading...</p>
      ) : apiInfo ? (
        <div className="info-card">
          <p><strong>API Name:</strong> {apiInfo.name}</p>
          <p><strong>Version:</strong> {apiInfo.version}</p>
          <p><strong>Status:</strong> {apiInfo.status}</p>
        </div>
      ) : (
        <p>Failed to connect to API</p>
      )}
    </div>
  )
}

export default Home
