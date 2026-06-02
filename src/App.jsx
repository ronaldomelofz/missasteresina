import { useState, useMemo } from 'react'
import igrejas from './data/igrejas.json'
import ChurchModal from './components/ChurchModal.jsx'

const DAYS = [
  { key: 'domingo', label: 'Dom' },
  { key: 'segunda', label: 'Seg' },
  { key: 'terca', label: 'Ter' },
  { key: 'quarta', label: 'Qua' },
  { key: 'quinta', label: 'Qui' },
  { key: 'sexta', label: 'Sex' },
  { key: 'sabado', label: 'Sáb' },
]

const TIME_OPTIONS = Array.from({ length: 48 }, (_, i) => i * 0.5)

// Retorna o dia atual da semana
function getTodayKey() {
  const map = ['domingo', 'segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado']
  return map[new Date().getDay()]
}

// Converte "18h30" → 18.5
function parseHour(str) {
  if (!str) return null
  const m = str.match(/(\d{1,2})h([0-5]\d)?/)
  if (!m) return null
  return parseInt(m[1], 10) + (m[2] ? parseInt(m[2], 10) / 60 : 0)
}

function getHoursFromText(str) {
  if (!str) return []
  const matches = [...str.matchAll(/(\d{1,2})h([0-5]\d)?/g)]
  return matches.map((m) => parseInt(m[1], 10) + (m[2] ? parseInt(m[2], 10) / 60 : 0))
}

// Verifica se algum horário da lista bate com o range
function hasActivityInRange(timesList, minH, maxH) {
  if (!timesList || timesList.length === 0) return false
  for (const t of timesList) {
    const hours = getHoursFromText(t)
    if (hours.length === 0) continue

    if (t.includes('às') && hours.length >= 2) {
      const start = Math.min(...hours)
      const end = Math.max(...hours)
      if (start <= maxH && end >= minH) return true
      continue
    }

    for (const h of hours) {
      if (h >= minH && h <= maxH) return true
    }
  }
  return false
}

function ChurchCard({ church, isOpen, onSelect }) {
  const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(church.nome + ' ' + church.bairro + ' Teresina PI')}`

  return (
    <div
      className={`church-card ${isOpen ? 'has-activity' : ''}`}
      onClick={() => onSelect(church)}
    >
      <div className="card-header">
        <h3 className="card-name">{church.nome}</h3>
        <span className={`card-open-badge ${isOpen ? 'badge-open' : 'badge-closed'}`}>
          {isOpen ? '● Ativo' : '○ Inativo'}
        </span>
      </div>

      <div className="card-address">
        <span>📍</span>
        <span>{church.bairro}</span>
      </div>

      {isOpen && (
        <div className="card-activities">
          {church._filteredMissas?.length > 0 && (
            <div className="activity-row missa">
              <span className="activity-icon">⛪</span>
              <span className="activity-label">Missa</span>
              <span className="activity-times">{church._filteredMissas.join(' · ')}</span>
            </div>
          )}
          {church._filteredConfissoes?.length > 0 && (
            <div className="activity-row confissao">
              <span className="activity-icon">🙏</span>
              <span className="activity-label">Confissão</span>
              <span className="activity-times">{church._filteredConfissoes.join(' · ')}</span>
            </div>
          )}
          {church._filteredAdoracao?.length > 0 && (
            <div className="activity-row adoracao">
              <span className="activity-icon">✨</span>
              <span className="activity-label">Adoração</span>
              <span className="activity-times">{church._filteredAdoracao.join(' · ')}</span>
            </div>
          )}
        </div>
      )}

      <div className="card-footer">
        <div className="card-links">
          <a
            href={mapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="card-link"
            onClick={e => e.stopPropagation()}
          >
            🗺️ Maps
          </a>
          {church.instagram && (
            <a
              href={`https://instagram.com/${church.instagram}`}
              target="_blank"
              rel="noopener noreferrer"
              className="card-link"
              onClick={e => e.stopPropagation()}
            >
              📷 IG
            </a>
          )}
        </div>
        {church.telefone && (
          <span className="card-phone">📞 {church.telefone}</span>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const [selectedDay, setSelectedDay] = useState(getTodayKey())
  const [timeMin, setTimeMin] = useState(0)
  const [timeMax, setTimeMax] = useState(23.5)
  const [showMissas, setShowMissas] = useState(true)
  const [showConfissoes, setShowConfissoes] = useState(true)
  const [showAdoracao, setShowAdoracao] = useState(true)
  const [onlyActive, setOnlyActive] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedChurch, setSelectedChurch] = useState(null)

  // Filtro principal
  const filtered = useMemo(() => {
    return igrejas
      .filter(church => {
        if (searchTerm) {
          const term = searchTerm.toLowerCase()
          if (
            !church.nome.toLowerCase().includes(term) &&
            !church.bairro.toLowerCase().includes(term) &&
            !church.endereco.toLowerCase().includes(term)
          ) return false
        }
        return true
      })
      .map(church => {
        const missasTimes = showMissas
          ? (church.missas?.[selectedDay] || []).filter(t => {
              const h = parseHour(t)
              return h !== null && h >= timeMin && h <= timeMax
            })
          : []

        const confissoesTimes = showConfissoes
          ? (church.confissoes?.[selectedDay] || []).filter(t =>
              hasActivityInRange([t], timeMin, timeMax)
            )
          : []

        const adoracaoTimes = showAdoracao
          ? (church.adoracao?.[selectedDay] || []).filter(t =>
              hasActivityInRange([t], timeMin, timeMax)
            )
          : []

        const isOpen = missasTimes.length > 0 || confissoesTimes.length > 0 || adoracaoTimes.length > 0

        return {
          ...church,
          _filteredMissas: missasTimes,
          _filteredConfissoes: confissoesTimes,
          _filteredAdoracao: adoracaoTimes,
          _isOpen: isOpen,
        }
      })
      .filter(church => !onlyActive || church._isOpen)
      .sort((a, b) => {
        if (a._isOpen && !b._isOpen) return -1
        if (!a._isOpen && b._isOpen) return 1
        return a.nome.localeCompare(b.nome)
      })
  }, [selectedDay, timeMin, timeMax, showMissas, showConfissoes, showAdoracao, onlyActive, searchTerm])

  const openCount = filtered.filter(c => c._isOpen).length

  function resetFilters() {
    setSelectedDay(getTodayKey())
    setTimeMin(0)
    setTimeMax(23.5)
    setShowMissas(true)
    setShowConfissoes(true)
    setShowAdoracao(true)
    setOnlyActive(false)
    setSearchTerm('')
  }

  const formatHour = (h) => `${String(Math.floor(h)).padStart(2, '0')}h${h % 1 !== 0 ? '30' : ''}`

  return (
    <>
      <header className="site-header">
        <div className="header-inner">
          <div className="header-brand">
            <img src="/brasao_arquidiocese_teresina.png" alt="Brasao da Arquidiocese de Teresina" className="header-shield" />
            <div>
              <div className="header-title">Missas Teresina</div>
            </div>
          </div>
        </div>
      </header>

      <div className="app-layout">
        {/* Painel de filtros */}
        <aside className="filters-panel">

          {/* Busca */}
          <div className="filter-card">
            <div className="filter-card-title">🔍 Buscar</div>
            <input
              type="text"
              className="search-input"
              placeholder="Igreja, bairro ou nome..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Dia da semana */}
          <div className="filter-card">
            <div className="filter-card-title">📅 Dia da Semana</div>
            <div className="days-grid">
              {DAYS.map(d => (
                <button
                  key={d.key}
                  className={`day-btn ${selectedDay === d.key ? 'active' : ''}`}
                  onClick={() => setSelectedDay(d.key)}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          {/* Horário */}
          <div className="filter-card">
            <div className="filter-card-title">⏰ Horário</div>
            <div className="time-range-display">
              <span>A partir de <span className="time-highlight">{formatHour(timeMin)}</span></span>
              <span>Até <span className="time-highlight">{formatHour(timeMax)}</span></span>
            </div>
            <div className="time-select-grid">
              <label>
                De
                <select
                  className="time-select"
                  value={timeMin}
                  onChange={e => {
                    const v = parseFloat(e.target.value)
                    setTimeMin(v)
                    if (v > timeMax) setTimeMax(v)
                  }}
                >
                  {TIME_OPTIONS.map(t => (
                    <option key={`min-${t}`} value={t}>{formatHour(t)}</option>
                  ))}
                </select>
              </label>
              <label>
                Até
                <select
                  className="time-select"
                  value={timeMax}
                  onChange={e => {
                    const v = parseFloat(e.target.value)
                    setTimeMax(v)
                    if (v < timeMin) setTimeMin(v)
                  }}
                >
                  {TIME_OPTIONS.map(t => (
                    <option key={`max-${t}`} value={t}>{formatHour(t)}</option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          {/* Tipo de atividade */}
          <div className="filter-card">
            <div className="filter-card-title">🕊️ Tipo de Atividade</div>
            <div className="activity-toggles">
              <div
                className={`toggle-item toggle-missa ${showMissas ? 'active' : ''}`}
                onClick={() => setShowMissas(v => !v)}
              >
                <div className="toggle-dot" />
                <span className="toggle-label">⛪ Missas</span>
              </div>
              <div
                className={`toggle-item toggle-confissao ${showConfissoes ? 'active' : ''}`}
                onClick={() => setShowConfissoes(v => !v)}
              >
                <div className="toggle-dot" />
                <span className="toggle-label">🙏 Confissões</span>
              </div>
              <div
                className={`toggle-item toggle-adoracao ${showAdoracao ? 'active' : ''}`}
                onClick={() => setShowAdoracao(v => !v)}
              >
                <div className="toggle-dot" />
                <span className="toggle-label">✨ Adoração</span>
              </div>
            </div>
          </div>

          {/* Resumo */}
          <div className="results-summary">
            <div className="results-count">
              <strong>{openCount}</strong> de {filtered.length} locais ativos
            </div>
            <button className="btn-reset" onClick={resetFilters}>
              Limpar filtros
            </button>
          </div>

          <label className="only-active-row">
            <input
              type="checkbox"
              checked={onlyActive}
              onChange={e => setOnlyActive(e.target.checked)}
            />
            <span>Mostrar apenas locais ativos</span>
          </label>

        </aside>

        {/* Área de conteúdo */}
        <main className="content-area">
          <div className="churches-grid">
            {filtered.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">⛪</div>
                <div className="empty-text">Nenhuma igreja encontrada com esses filtros</div>
              </div>
            ) : (
              filtered.map(church => (
                <ChurchCard
                  key={church.id}
                  church={church}
                  isOpen={church._isOpen}
                  onSelect={setSelectedChurch}
                />
              ))
            )}
          </div>
        </main>
      </div>

      <footer className="site-footer">
        <div className="footer-shields">
          <img src="/brasao_arquidiocese_teresina.png" alt="Brasao da Arquidiocese de Teresina" className="footer-shield-arch" />
        </div>
        <span className="footer-cross">✝</span>
        Dados extraídos da Arquidiocese de Teresina — Centro Pastoral Paulo VI · Atualizado em 17/04/2026
        <br />
        Horários sujeitos a alterações. Confirme com a paróquia.
      </footer>

      {/* Modal */}
      {selectedChurch && (
        <ChurchModal
          church={selectedChurch}
          onClose={() => setSelectedChurch(null)}
        />
      )}
    </>
  )
}
