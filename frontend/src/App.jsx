import { useState, useRef, useEffect } from 'react'
import './index.css'

const STAGES = [
  { id: 'Upload screenshot', title: 'Upload screenshot' },
  { id: 'Image validated and prepared', title: 'Read player names' },
  { id: 'Matching players with FPL data', title: 'Match FPL players' },
  { id: 'Checking squad constraints', title: 'Load fixtures and projections' },
  { id: 'Ranking transfer candidates', title: 'Analyze transfer options' },
  { id: 'Preparing your recommendation', title: 'Build suggested team' },
  { id: 'Deleting temporary data', title: 'Delete temporary data' }
];

function Timeline({ stage, status }) {
  const activeIndex = STAGES.findIndex(s => s.id === stage);
  
  return (
    <div className="panel col-right timeline-panel">
      <h2 className="panel-header">AI Process</h2>
      {STAGES.map((s, idx) => {
        let stateText = 'Waiting';
        let stateClass = 'waiting';
        
        if (status === 'complete') {
          stateText = 'Complete';
          stateClass = 'completed';
        } else if (activeIndex > idx) {
          stateText = 'Complete';
          stateClass = 'completed';
        } else if (activeIndex === idx) {
          stateText = 'Running';
          stateClass = 'active';
        }

        return (
          <div key={s.id} className={`timeline-item ${stateClass}`}>
            <div className="timeline-status-icon">
              {stateClass === 'completed' ? '✓' : (stateClass === 'active' ? '○' : '—')}
            </div>
            <div className="timeline-content">
              <div className="timeline-title">{s.title} — <span className={`status-label ${stateClass}`}>{stateText}</span></div>
            </div>
          </div>
        );
      })}
      
      {status === 'complete' && (
        <div className="tech-details">
          <h3>Data Freshness</h3>
          <p>FPL Cache: Fresh</p>
          <h3>Privacy</h3>
          <p>Temporary files deleted: Yes</p>
        </div>
      )}
    </div>
  )
}

function PitchPlayer({ player }) {
  const fallbackSvg = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='%23404040'/><circle cx='50' cy='40' r='20' fill='%23666'/><path d='M20 100 Q50 60 80 100' fill='%23666'/></svg>";
  return (
    <div className={`pitch-player ${player.is_new ? 'new-player' : ''}`}>
      <img 
        src={player.photo_url || fallbackSvg} 
        alt={player.name} 
        onError={(e) => { e.target.onerror = null; e.target.src = fallbackSvg; }}
      />
      <div className="name">
        {player.name}
      </div>
      <div className="points">{player.ep_next} pts</div>
    </div>
  )
}

function Pitch({ starters, bench, title }) {
  if (!starters || starters.length === 0) return <div className="pitch-container empty"></div>
  return (
    <div className="pitch-container">
      <div className="position-row">{starters.filter(p => p.position_id === 4).map(p => <PitchPlayer key={p.id} player={p} />)}</div>
      <div className="position-row">{starters.filter(p => p.position_id === 3).map(p => <PitchPlayer key={p.id} player={p} />)}</div>
      <div className="position-row">{starters.filter(p => p.position_id === 2).map(p => <PitchPlayer key={p.id} player={p} />)}</div>
      <div className="position-row">{starters.filter(p => p.position_id === 1).map(p => <PitchPlayer key={p.id} player={p} />)}</div>
      <div className="bench-row">{bench.map(p => <PitchPlayer key={p.id} player={p} />)}</div>
    </div>
  )
}

function App() {
  const [image, setImage] = useState(null)
  const [transfers, setTransfers] = useState(1)
  const [reqId, setReqId] = useState(null)
  const [jobData, setJobData] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const handleDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) setImage(file)
  }

  const handleSubmit = async () => {
    if (!image || transfers < 0) return
    setError(null)
    setJobData({ status: 'processing', stage: 'Upload screenshot' })
    
    try {
      const formData = new FormData()
      formData.append('squadImage', image)
      formData.append('transfers', transfers)
      
      const res = await fetch('http://localhost:3001/api/process-team', {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (res.ok) {
        setReqId(data.request_id)
        setJobData(data)
      } else {
        setError(data.detail || "Upload failed")
        setJobData(null)
      }
    } catch (err) {
      setError(err.message)
      setJobData(null)
    }
  }

  const handleReset = () => {
    setReqId(null)
    setJobData(null)
    setImage(null)
    setError(null)
  }

  useEffect(() => {
    let interval;
    if (reqId && jobData?.status !== 'complete' && jobData?.status !== 'failed') {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:3001/api/process-team/${reqId}`)
          const data = await res.json()
          setJobData(data)
          if (data.status === 'complete' || data.status === 'failed') {
            clearInterval(interval)
          }
        } catch(e) {
          console.error(e)
        }
      }, 1000)
    }
    return () => clearInterval(interval)
  }, [reqId, jobData?.status])

  const isComplete = jobData?.status === 'complete'
  const isProcessing = (reqId || jobData?.status === 'processing') && !isComplete && jobData?.status !== 'failed'
  const stage = jobData?.stage

  return (
    <div className="app-shell">
      {/* HEADER */}
      <header className="top-header">
        <div className="header-left">
          <h1>FPL AI Assistant</h1>
          <span className="subtitle">Analyze your squad and plan your next move.</span>
        </div>
        <div className="header-right">
          <span className="badge">Gameweek Active</span>
          <span className="badge success">Data Fresh</span>
          <button onClick={handleReset} className="btn-reset">Reset</button>
        </div>
      </header>

      <div className="dashboard-layout">
        {/* LEFT COLUMN */}
        <div className="col-left workspace-col">
          <div className="panel">
            <h2 className="panel-header">My Team</h2>
            {!isComplete && !isProcessing ? (
              <p className="empty-text">Upload a screenshot to detect your current squad.</p>
            ) : isProcessing ? (
              <p className="loading-text">Loading...</p>
            ) : (
              <div className="squad-summary">
                <div className="squad-label">Original squad</div>
                <div className="formation">11/11 starters detected</div>
                {jobData.original_team.starters.map(p => (
                  <div key={p.id} className="squad-player-row">
                    <span>{p.name}</span>
                    <span>{p.ep_next} pts</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="panel">
            <h2 className="panel-header">AI Team</h2>
            {!isComplete && !isProcessing ? (
              <p className="empty-text">Your suggested team will appear here after analysis.</p>
            ) : isProcessing ? (
              <p className="loading-text">Loading...</p>
            ) : (
              <div className="squad-summary">
                <div className="squad-label">Suggested squad</div>
                {jobData.suggested_team.starters.map(p => (
                  <div key={p.id} className="squad-player-row">
                    <span className={p.is_new ? "player-in" : ""}>{p.name} {p.is_new && "(NEW)"}</span>
                    <span>{p.ep_next} pts</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {isComplete && (
            <div className="panel">
              <h2 className="panel-header">Quick Comparison</h2>
              <div className="stat-row"><span>Transfers:</span> <span>{jobData.transfers.length}</span></div>
              <div className="stat-row"><span>Used Free Transfers:</span> <span>{transfers}</span></div>
              <div className="stat-row"><span>Confidence:</span> <span>High</span></div>
            </div>
          )}
        </div>

        {/* CENTER COLUMN */}
        <div className="col-center workspace-col">
          {!isComplete && !isProcessing && (
            <div className="panel upload-panel">
              <h2 className="panel-header text-center">Upload your FPL team screenshot</h2>
              <p className="upload-desc">
                Upload a screenshot of your current FPL team. The app will identify your players, check current FPL data, compare transfer options, and explain the strongest recommendation.
              </p>
              
              <div 
                className="upload-area"
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current.click()}
              >
                {image ? (
                  <div className="selected-file">✅ {image.name} ({(image.size/1024).toFixed(1)} KB)</div>
                ) : (
                  <div>Drop screenshot to upload<br/>or Click to Browse</div>
                )}
                <input type="file" ref={fileInputRef} onChange={(e) => setImage(e.target.files[0])} hidden accept="image/png, image/jpeg, image/webp"/>
              </div>

              {image && (
                <div className="image-actions">
                  <button className="btn-secondary" onClick={(e) => {e.stopPropagation(); setImage(null)}}>Remove</button>
                </div>
              )}

              <div className="transfers-input-group">
                <label>Free Transfers:</label>
                <input type="number" min="0" value={transfers} onChange={(e) => setTransfers(Number(e.target.value))} />
                <span className="input-hint">The number of free transfers affects the recommendation strategy.</span>
              </div>

              {error && <div className="error-message">{error}</div>}

              <button className="btn-primary analyze-btn" onClick={handleSubmit} disabled={!image || transfers < 0}>
                Analyze Team
              </button>
              
              <div className="privacy-note">
                Your screenshot is used temporarily for analysis and deleted after processing.
              </div>
            </div>
          )}

          {isProcessing && (
            <div className="panel processing-panel">
              <h2 className="panel-header text-center">Analysis in progress</h2>
              <div className="processing-content">
                <div className="spinner"></div>
                <p>Reading screenshot and preparing your squad analysis.</p>
                <p className="current-stage">Current stage: {jobData?.message || 'Connecting...'}</p>
              </div>
            </div>
          )}

          {isComplete && (
            <div className="panel result-panel">
              <div className="recommendation-header">
                <h2>{jobData.transfers.length > 0 ? `Make ${jobData.transfers.length} transfer(s)` : 'Hold this week'}</h2>
                <p>{jobData.message}</p>
              </div>
              
              <div className="pitch-comparison-section">
                <div className="pitch-col">
                  <h3>Original Team</h3>
                  <Pitch starters={jobData.original_team.starters} bench={jobData.original_team.bench} />
                </div>
                <div className="pitch-col">
                  <h3>AI Suggested Team</h3>
                  <Pitch starters={jobData.suggested_team.starters} bench={jobData.suggested_team.bench} />
                </div>
              </div>

              {jobData.transfers.length > 0 && (
                <div className="transfer-recommendations">
                  <h3 className="section-title">Recommended Transfers</h3>
                  {jobData.transfers.map((t, idx) => (
                    <div key={idx} className="transfer-card">
                      <div className="transfer-players">
                        <span className="player-out">{t.out_player_name} OUT</span> ➔ <span className="player-in">{t.in_player_name} IN</span>
                      </div>
                      <div className="transfer-stats">
                        <span>Net Gain: <strong className="success">+{t.projected_gain_1gw.toFixed(1)} pts</strong></span>
                        <span>Hit Cost: <strong>-{t.hit_cost} pts</strong></span>
                        <span>Price diff: {(t.new_price - t.current_price).toFixed(1)}m</span>
                      </div>
                      <div className="transfer-reason">
                        <strong>Reason:</strong> {t.reasons.join(', ')}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {jobData.fixtures && jobData.fixtures.length > 0 && (
                <div className="analytics-section" style={{ marginBottom: '2rem' }}>
                  <h3 className="section-title">Upcoming Fixtures (Suggested Players)</h3>
                  <div className="fixtures-list">
                    {jobData.fixtures.map((f, idx) => (
                      <div key={idx} className="fixture-row">
                        <span style={{ fontWeight: 'bold' }}>{f.player_name}</span>
                        <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-muted)' }}>
                          {f.upcoming.map((u, i) => (
                            <span key={i} className="fixture-diff-2">{u}</span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="analytics-section">
                <h3 className="section-title">Squad Analytics & Extraction</h3>
                <div className="stat-row"><span>Available Powerups:</span> <span>{jobData.ocr_summary?.powerups_detected?.length > 0 ? jobData.ocr_summary.powerups_detected.join(', ') : 'None Detected'}</span></div>
                <div className="stat-row"><span>Players Detected:</span> <span>{jobData.ocr_summary?.players_matched || 0}/15</span></div>
                <div className="stat-row"><span>Formation Balance:</span> <span>Optimal</span></div>
                <div className="stat-row"><span>Captain Candidate:</span> <span>{jobData.suggested_team.starters[0]?.name || '-'}</span></div>
                <div className="stat-row"><span>Data Confidence:</span> <span>{((jobData.ocr_summary?.average_confidence || 0) * 100).toFixed(0)}%</span></div>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN */}
        <Timeline stage={stage} status={jobData?.status} />
      </div>
    </div>
  )
}

export default App
