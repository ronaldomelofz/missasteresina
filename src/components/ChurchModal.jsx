const DAYS_LABELS = {
  domingo: 'Domingo',
  segunda: 'Segunda',
  terca: 'Terça',
  quarta: 'Quarta',
  quinta: 'Quinta',
  sexta: 'Sexta',
  sabado: 'Sábado',
}

const ALL_DAYS = ['domingo', 'segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado']

export default function ChurchModal({ church, onClose }) {
  if (!church) return null

  const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(church.nome + ' ' + church.bairro + ' Teresina PI')}`
  const instagramUrl = church.instagram ? `https://instagram.com/${church.instagram}` : null

  const hasMissas = ALL_DAYS.some(d => church.missas?.[d]?.length > 0)
  const hasConfissoes = ALL_DAYS.some(d => church.confissoes?.[d]?.length > 0)
  const hasAdoracao = ALL_DAYS.some(d => church.adoracao?.[d]?.length > 0)

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-box">
        <div className="modal-header">
          <div className="modal-cross">✝</div>
          <h2 className="modal-title">{church.nome}</h2>
          <p className="modal-address">📍 {church.endereco} · {church.bairro}</p>
          <button className="modal-close" onClick={onClose} aria-label="Fechar">✕</button>
        </div>

        <div className="modal-body">
          {/* Missas */}
          {hasMissas && (
            <div className="modal-section">
              <h3 className="modal-section-title">⛪ Horários de Missa</h3>
              <table className="schedule-table">
                <thead>
                  <tr>
                    <th>Dia</th>
                    <th>Horários</th>
                  </tr>
                </thead>
                <tbody>
                  {ALL_DAYS.map(day => {
                    const times = church.missas?.[day]
                    if (!times || times.length === 0) return null
                    return (
                      <tr key={day}>
                        <td className="day-name">{DAYS_LABELS[day]}</td>
                        <td>
                          <div className="times-cell">
                            {times.map((t, i) => (
                              <span key={i} className="time-chip missa">{t}</span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Confissões */}
          {hasConfissoes && (
            <div className="modal-section">
              <h3 className="modal-section-title">🙏 Confissões</h3>
              <table className="schedule-table">
                <thead>
                  <tr>
                    <th>Dia</th>
                    <th>Horários</th>
                  </tr>
                </thead>
                <tbody>
                  {ALL_DAYS.map(day => {
                    const times = church.confissoes?.[day]
                    if (!times || times.length === 0) return null
                    return (
                      <tr key={day}>
                        <td className="day-name">{DAYS_LABELS[day]}</td>
                        <td>
                          <div className="times-cell">
                            {times.map((t, i) => (
                              <span key={i} className="time-chip confissao">{t}</span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Adoração */}
          {hasAdoracao && (
            <div className="modal-section">
              <h3 className="modal-section-title">✨ Adoração / Exposição do Santíssimo</h3>
              <table className="schedule-table">
                <thead>
                  <tr>
                    <th>Dia</th>
                    <th>Horários</th>
                  </tr>
                </thead>
                <tbody>
                  {ALL_DAYS.map(day => {
                    const times = church.adoracao?.[day]
                    if (!times || times.length === 0) return null
                    return (
                      <tr key={day}>
                        <td className="day-name">{DAYS_LABELS[day]}</td>
                        <td>
                          <div className="times-cell">
                            {times.map((t, i) => (
                              <span key={i} className="time-chip adoracao">{t}</span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Contato */}
          <div className="modal-section">
            <h3 className="modal-section-title">📞 Contato & Localização</h3>
            <div className="modal-actions">
              <a
                href={mapsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary"
              >
                🗺️ Abrir no Google Maps
              </a>
              {church.telefone && (
                <a
                  href={`tel:+55${church.telefone.replace(/\D/g, '')}`}
                  className="btn-secondary"
                >
                  📞 {church.telefone}
                </a>
              )}
              {instagramUrl && (
                <a
                  href={instagramUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary"
                >
                  📷 Instagram
                </a>
              )}
            </div>
          </div>

          <p style={{ fontSize: '0.7rem', color: 'var(--ink-faint)', marginTop: '8px' }}>
            ⚠️ Horários sujeitos a alterações. Confirme com a paróquia antes de ir.
          </p>
        </div>
      </div>
    </div>
  )
}
