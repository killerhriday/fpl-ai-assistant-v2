import { useState, useEffect } from 'react'
import squadData from './squad.json'
import allPlayersData from './all_players.json'
import './index.css'

function PlayerCard({ player, isList, isSelected, onClick }) {
  // Use a fallback image if photo_url is missing
  const imgUrl = player.photo_url || "https://resources.premierleague.com/premierleague/photos/players/110x140/Photo-Missing.png"

  return (
    <div 
      className={`player-card ${isList ? 'is-list' : ''} ${isSelected ? 'selected' : ''}`}
      onClick={() => onClick(player)}
      style={{
        borderColor: isSelected ? '#eab308' : '',
        boxShadow: isSelected ? '0 0 15px rgba(234, 179, 8, 0.6)' : ''
      }}
    >
      <img src={imgUrl} alt={player.name} className="player-photo" loading="lazy" onError={(e) => e.target.src="https://resources.premierleague.com/premierleague/photos/players/110x140/Photo-Missing.png"} />
      <div className="player-info">
        <div className="player-name">{player.name}</div>
        <div className="player-team">{player.team_name}</div>
      </div>
      <div className="player-stats">
        <span className="cost">£{player.cost.toFixed(1)}m</span>
        <span className="xpts">{player.ep_next.toFixed(1)} pts</span>
      </div>
    </div>
  )
}

function App() {
  const [starters, setStarters] = useState([])
  const [bench, setBench] = useState([])
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    // Initial optimal squad from python JSON
    const gk = squadData.filter(p => p.position_id === 1).sort((a,b) => b.ep_next - a.ep_next)
    const def = squadData.filter(p => p.position_id === 2).sort((a,b) => b.ep_next - a.ep_next)
    const mid = squadData.filter(p => p.position_id === 3).sort((a,b) => b.ep_next - a.ep_next)
    const fwd = squadData.filter(p => p.position_id === 4).sort((a,b) => b.ep_next - a.ep_next)

    const s = [
      gk[0],
      def[0], def[1], def[2],
      mid[0], mid[1], mid[2], mid[3],
      fwd[0], fwd[1], fwd[2]
    ]
    const b = [
      gk[1],
      def[3], def[4],
      mid[4]
    ]
    
    setStarters(s)
    setBench(b)
  }, [])

  const isPlayerInSquad = (playerId) => {
    return starters.some(p => p.id === playerId) || bench.some(p => p.id === playerId)
  }

  const handleSquadPlayerClick = (player) => {
    if (selectedPlayer && selectedPlayer.id === player.id) {
      setSelectedPlayer(null) // deselect
      return
    }

    if (selectedPlayer && isPlayerInSquad(selectedPlayer.id)) {
      // Swap two squad players (e.g. Starter <-> Bench)
      const isSelectedStarter = starters.find(p => p.id === selectedPlayer.id)
      const isClickedStarter = starters.find(p => p.id === player.id)

      if (isSelectedStarter && !isClickedStarter) {
        swapSquadPlayers(selectedPlayer, player)
      } else if (!isSelectedStarter && isClickedStarter) {
        swapSquadPlayers(player, selectedPlayer)
      } else {
        setSelectedPlayer(player) // Just change selection
      }
    } else {
      // Either nothing selected, or an index player selected
      if (selectedPlayer && !isPlayerInSquad(selectedPlayer.id)) {
        // We selected an Index player, now clicked a Squad player to transfer them in
        transferPlayer(player, selectedPlayer)
      } else {
        setSelectedPlayer(player)
      }
    }
  }

  const handleIndexPlayerClick = (player) => {
    if (isPlayerInSquad(player.id)) return; // Already in squad

    if (selectedPlayer && isPlayerInSquad(selectedPlayer.id)) {
      // We selected a Squad player, now clicked an Index player to transfer them in
      transferPlayer(selectedPlayer, player)
    } else {
      // Just select the index player
      setSelectedPlayer(player)
    }
  }

  const swapSquadPlayers = (starter, benched) => {
    setStarters(starters.map(p => p.id === starter.id ? benched : p))
    setBench(bench.map(p => p.id === benched.id ? starter : p))
    setSelectedPlayer(null)
  }

  const transferPlayer = (outPlayer, inPlayer) => {
    // Only allow transfer if same position (to keep constraints simple for UI)
    if (outPlayer.position_id !== inPlayer.position_id) {
      alert("Please select a player of the same position to transfer.")
      return
    }
    
    if (starters.some(p => p.id === outPlayer.id)) {
      setStarters(starters.map(p => p.id === outPlayer.id ? inPlayer : p))
    } else {
      setBench(bench.map(p => p.id === outPlayer.id ? inPlayer : p))
    }
    setSelectedPlayer(null)
  }

  const startingXPts = starters.reduce((sum, p) => sum + p.ep_next, 0)
  const totalCost = [...starters, ...bench].reduce((sum, p) => sum + p.cost, 0)
  const isOverBudget = totalCost > 100.0

  // Filter the index
  const filteredIndex = allPlayersData.filter(p => {
    if (isPlayerInSquad(p.id)) return false
    if (!searchQuery) return true
    return p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
           p.team_name.toLowerCase().includes(searchQuery.toLowerCase())
  }).sort((a,b) => b.ep_next - a.ep_next).slice(0, 100) // limit to 100 for perf

  return (
    <div>
      <div className="header">
        <h1>FPL Optimizer V2</h1>
        <p>Transfer & Tinker. Tap a player in your team, then tap a player in the index to transfer them.</p>
      </div>

      <div className="dashboard">
        <div className="stat-box">
          <div className="stat-label">Total Squad Value</div>
          <div className={`stat-value ${isOverBudget ? 'error' : ''}`}>
            £{totalCost.toFixed(1)}m
          </div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Starting XI Points</div>
          <div className="stat-value">{startingXPts.toFixed(1)}</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Budget Remaining</div>
          <div className={`stat-value ${isOverBudget ? 'error' : ''}`}>
            £{(100.0 - totalCost).toFixed(1)}m
          </div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Formation</div>
          <div className="stat-value">
            {starters.filter(p => p.position_id===2).length}-
            {starters.filter(p => p.position_id===3).length}-
            {starters.filter(p => p.position_id===4).length}
          </div>
        </div>
      </div>

      <div className="app-container">
        
        {/* PITCH */}
        <div className="pitch-container">
          {/* Forwards */}
          <div className="position-row">
            {starters.filter(p => p.position_id === 4).map(p => (
              <PlayerCard key={p.id} player={p} isSelected={selectedPlayer?.id === p.id} onClick={handleSquadPlayerClick} />
            ))}
          </div>
          {/* Midfielders */}
          <div className="position-row">
            {starters.filter(p => p.position_id === 3).map(p => (
              <PlayerCard key={p.id} player={p} isSelected={selectedPlayer?.id === p.id} onClick={handleSquadPlayerClick} />
            ))}
          </div>
          {/* Defenders */}
          <div className="position-row">
            {starters.filter(p => p.position_id === 2).map(p => (
              <PlayerCard key={p.id} player={p} isSelected={selectedPlayer?.id === p.id} onClick={handleSquadPlayerClick} />
            ))}
          </div>
          {/* Goalkeepers */}
          <div className="position-row">
            {starters.filter(p => p.position_id === 1).map(p => (
              <PlayerCard key={p.id} player={p} isSelected={selectedPlayer?.id === p.id} onClick={handleSquadPlayerClick} />
            ))}
          </div>
        </div>

        {/* BENCH */}
        <div className="side-panel">
          <h2>Your Bench</h2>
          <div className="instructions">
            Tap a starter, then tap a bench player to substitute.
          </div>
          {bench.map(p => (
            <PlayerCard key={p.id} player={p} isList={true} isSelected={selectedPlayer?.id === p.id} onClick={handleSquadPlayerClick} />
          ))}
        </div>

        {/* INDEX */}
        <div className="side-panel">
          <h2>Player Database</h2>
          <div className="instructions">
            Tap a player in your team, then tap a player here to Transfer. (Same position only)
          </div>
          <input 
            type="text" 
            className="search-input" 
            placeholder="Search player or team..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {filteredIndex.map(p => (
            <PlayerCard key={p.id} player={p} isList={true} isSelected={selectedPlayer?.id === p.id} onClick={handleIndexPlayerClick} />
          ))}
        </div>

      </div>
    </div>
  )
}

export default App
