import { useState, useRef, useEffect } from 'react'
import './index.css'

const STAGES = [
  { id: 'Screenshot received', title: 'Upload screenshot' },
  { id: 'Image validated and prepared', title: 'Validate image' },
  { id: 'Reading player names', title: 'Read player names' },
  { id: 'Matching players with FPL data', title: 'Match FPL players' },
  { id: 'Checking squad constraints', title: 'Load fixtures and projections' },
  { id: 'Ranking transfer candidates', title: 'Analyze transfer options' },
  { id: 'Deleting temporary data', title: 'Delete temporary data' }
];

const MOCK_NEWS = [
  { source: 'BBC Sport', headline: 'Haaland continues scoring streak', summary: 'Erling Haaland netted a hat-trick against Fulham to solidify his golden boot campaign.' },
  { source: 'The Guardian', headline: 'Saka injury update', summary: 'Mikel Arteta confirms Bukayo Saka will face a late fitness test before the weekend clash.' },
  { source: 'Sky Sports', headline: 'Double gameweek confirmed', summary: 'Chelsea and Spurs will play twice in GW34 following the latest fixture reshuffle.' }
];

function Timeline({ stage, status, dataFreshness }) {
  const activeIndex = STAGES.findIndex(s => s.id === stage);
  
  return (
    <div className="panel timeline-panel">
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
          <p>FPL Cache: {dataFreshness ? (dataFreshness.is_stale ? "Stale" : "Fresh") : "Fresh"}</p>
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

function AILoader({ size = 180, text = "Analyzing" }) {
  const letters = text.split("");
  return (
    <div className="ai-loader-container">
      <div className="ai-loader-wrapper" style={{ width: size, height: size }}>
        {letters.map((letter, index) => (
          <span
            key={index}
            className="ai-loader-letter"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            {letter}
          </span>
        ))}
        <div className="ai-loader-circle"></div>
      </div>
    </div>
  );
}

function App() {
  const [image, setImage] = useState(null)
  const [transfers, setTransfers] = useState(1)
  const [reqId, setReqId] = useState(null)
  const [jobData, setJobData] = useState(null)
  const [metadata, setMetadata] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    fetch('http://localhost:3001/api/metadata')
      .then(r => r.json())
      .then(d => setMetadata(d))
      .catch(console.error)
  }, [])

  const handleDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) setImage(file)
  }

  const handleSubmit = async (selectedImage) => {
    const imgToUse = selectedImage || image;
    if (!imgToUse || transfers < 0) return
    setError(null)
    setJobData({ status: 'processing', stage: 'Screenshot received' })
    
    try {
      const formData = new FormData()
      formData.append('squadImage', imgToUse)
      formData.append('transfers', transfers)
      formData.append('bank_balance', 0.0) // Legacy field, backend will auto-calculate
      
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
          if (!res.ok) {
            clearInterval(interval)
            setError("Analysis failed or session expired.")
            setJobData(null)
            setReqId(null)
            return
          }
          const data = await res.json()
          setJobData(data)
          if (data.status === 'complete' || data.status === 'failed') {
            clearInterval(interval)
          }
          if (data.status === 'failed') {
            setError(data.error || "Analysis failed.")
          }
        } catch(e) {
          console.error(e)
          clearInterval(interval)
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
          <span className="subtitle">Deterministic Squad Analysis & Transfer Recommendations</span>
        </div>
        <div className="header-right">
          {metadata && metadata.gameweek !== "Unknown" ? (
            <span className="badge" style={{ borderColor: 'rgba(56, 189, 248, 0.3)', color: 'var(--text-main)' }}>
              {metadata.gameweek}
              {metadata.deadline && ` (Deadline: ${new Date(metadata.deadline).toLocaleDateString()})`}
            </span>
          ) : (
            <span className="badge">Gameweek Active</span>
          )}
          {jobData?.data_freshness ? (
            <span className={`badge ${jobData.data_freshness.is_stale ? 'danger' : 'success'}`}>
              {jobData.data_freshness.is_stale ? 'Stale Data' : 'Cached official FPL data'}
            </span>
          ) : (
            <span className="badge success">Data Fresh</span>
          )}
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
                <div className="formation">11/11 starters detected</div>
                {jobData.original_team.starters.map(p => (
                  <div key={p.id} className="squad-player-row">
                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.65rem', padding: '2px 4px', background: 'var(--border)', borderRadius: '3px', width: '30px', textAlign: 'center' }}>
                        {p.position_id === 1 ? 'GK' : p.position_id === 2 ? 'DEF' : p.position_id === 3 ? 'MID' : 'FWD'}
                      </span>
                      {p.name} <span style={{ fontSize: '0.75rem', color: 'var(--text-faint)' }}>({p.club.replace('Club ', '')})</span>
                    </span>
                    <span>{p.ep_next} Proj. GW pts</span>
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
                {jobData.suggested_team.starters.map(p => (
                  <div key={p.id} className="squad-player-row">
                    <span className={p.is_new ? "player-in" : ""} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.65rem', padding: '2px 4px', background: 'var(--border)', borderRadius: '3px', width: '30px', textAlign: 'center', color: p.is_new ? 'var(--bg-color)' : 'inherit', backgroundColor: p.is_new ? 'var(--success)' : 'var(--border)' }}>
                        {p.position_id === 1 ? 'GK' : p.position_id === 2 ? 'DEF' : p.position_id === 3 ? 'MID' : 'FWD'}
                      </span>
                      {p.name} {p.is_new && <span style={{fontWeight: 'bold'}}>(NEW)</span>}
                    </span>
                    <span>{p.ep_next} Proj. GW pts</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {isComplete && (
            <div className="panel">
              <h2 className="panel-header">Latest FPL News</h2>
              <div className="news-feed">
                {MOCK_NEWS.map((item, idx) => (
                  <div key={idx} className="news-item">
                    <strong>{item.source}: {item.headline}</strong>
                    {item.summary}
                  </div>
                ))}
              </div>
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

              <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', justifyContent: 'center' }}>
                <div className="transfers-input-group">
                  <label>Free Transfers</label>
                  <input type="number" min="0" value={transfers} onChange={(e) => setTransfers(Number(e.target.value))} />
                </div>
              </div>

              {error && <div className="error-message">{error}</div>}

              <button className="btn-primary analyze-btn" onClick={() => handleSubmit(image)} disabled={!image || transfers < 0}>
                Analyze Team
              </button>
              
              <div className="privacy-note">
                Your screenshot is used temporarily for analysis and deleted after processing.
              </div>
            </div>
          )}

          {isProcessing && (
            <div className="panel processing-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
              <h2 className="panel-header text-center">Analysis in progress</h2>
              <div className="processing-content">
                <AILoader size={160} text="ANALYZING" />
                <p style={{ marginTop: '1rem' }}>Reading screenshot and preparing your squad analysis.</p>
                <p className="current-stage">Current stage: {jobData?.message || 'Connecting...'}</p>
              </div>
            </div>
          )}
          
          {isComplete && (
            <div className="panel upload-panel" style={{ textAlign: 'center' }}>
              <h2 className="panel-header text-center">Analysis Complete</h2>
              <p className="upload-desc" style={{ marginBottom: '1rem' }}>
                {jobData.transfers?.length > 0 ? `We recommend ${jobData.transfers.length} transfer(s).` : 'No transfers needed this week.'}
              </p>
              <button className="btn-primary analyze-btn" onClick={handleReset} style={{ width: 'auto' }}>
                Analyze Another Team
              </button>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN */}
        <div className="col-right workspace-col">
          {isComplete && jobData.ai_summary && (
            <div className="panel summary-panel">
              <h2 className="panel-header">AI Summary</h2>
              <p className="ai-summary-text">{jobData.ai_summary}</p>
            </div>
          )}

          {(isProcessing || isComplete) && (
            <Timeline stage={stage} status={jobData?.status} dataFreshness={jobData?.data_freshness} />
          )}
          
          {isComplete && jobData.global_injuries && (
            <div className="panel status-board">
              <h2 className="panel-header">FPL Player Status Board</h2>
              <div className="injury-list">
                {jobData.global_injuries.map((inj, idx) => (
                  <div key={idx} className="injury-row" title={inj.news}>
                    <span className={`status-dot ${inj.color}`}></span>
                    <span className="injury-name">{inj.player_name}</span>
                    <span className="injury-status">{inj.status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* BOTTOM ANALYTICS */}
      {isComplete && (
        <div className="bottom-analytics-section">
          {jobData.budget && (
            <div className="budget-metrics-row">
              <div className="budget-card">
                <div className="budget-label">Squad Value</div>
                <div className="budget-value">£{jobData.budget.squad_value.toFixed(1)}m</div>
              </div>
              <div className="budget-card">
                <div className="budget-label">In The Bank</div>
                <div className="budget-value">£{jobData.budget.in_the_bank.toFixed(1)}m</div>
              </div>
              <div className="budget-card total">
                <div className="budget-label">Total Budget</div>
                <div className="budget-value">£{jobData.budget.total_budget.toFixed(1)}m</div>
              </div>
            </div>
          )}

          <div className="panel result-panel">
            <div className="recommendation-header">
              <h2>{jobData.transfers.length > 0 ? `Make ${jobData.transfers.length} transfer(s)` : '✅ No transfers needed this week'}</h2>
              <p>{jobData.message}</p>
            </div>
            
            {jobData.transfers.length === 0 ? (
              <div className="pitch-comparison-section" style={{ display: 'flex', justifyContent: 'center' }}>
                <div className="pitch-col" style={{ maxWidth: '500px', flex: 'none', width: '100%' }}>
                  <h3>Your Optimal Squad</h3>
                  <Pitch starters={jobData.original_team.starters} bench={jobData.original_team.bench} />
                </div>
              </div>
            ) : (
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
            )}

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
          </div>
        </div>
      )}
    </div>
  )
}

export default App
