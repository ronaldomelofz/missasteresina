import { useEffect, useRef } from 'react'
import L from 'leaflet'

// Fix para ícones do Leaflet com Vite
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

function createCustomIcon(isOpen) {
  const color = isOpen ? '#2D7A4F' : '#B5620A'
  const svgIcon = `
    <svg width="28" height="38" viewBox="0 0 28 38" xmlns="http://www.w3.org/2000/svg">
      <path d="M14 0C6.27 0 0 6.27 0 14c0 9.75 14 24 14 24S28 23.75 28 14C28 6.27 21.73 0 14 0z" fill="${color}" opacity="0.95"/>
      <circle cx="14" cy="14" r="6" fill="white" opacity="0.9"/>
      <text x="14" y="18" text-anchor="middle" font-size="9" font-family="sans-serif" fill="${color}" font-weight="bold">✞</text>
    </svg>
  `
  return L.divIcon({
    html: svgIcon,
    className: '',
    iconSize: [28, 38],
    iconAnchor: [14, 38],
    popupAnchor: [0, -38],
  })
}

export default function MapView({ churches, filteredIds, onSelectChurch }) {
  const mapRef = useRef(null)
  const instanceRef = useRef(null)
  const markersRef = useRef({})

  useEffect(() => {
    if (!mapRef.current || instanceRef.current) return

    instanceRef.current = L.map(mapRef.current, {
      center: [-5.092, -42.802],
      zoom: 12,
      zoomControl: true,
    })

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(instanceRef.current)

    return () => {
      if (instanceRef.current) {
        instanceRef.current.remove()
        instanceRef.current = null
      }
    }
  }, [])

  useEffect(() => {
    if (!instanceRef.current) return

    // Remove marcadores antigos
    Object.values(markersRef.current).forEach(m => m.remove())
    markersRef.current = {}

    churches.forEach(church => {
      if (!church.lat || !church.lng) return

      const isOpen = filteredIds.has(church.id)
      const icon = createCustomIcon(isOpen)

      const marker = L.marker([church.lat, church.lng], { icon })

      const popupContent = document.createElement('div')
      popupContent.innerHTML = `
        <div class="popup-name">${church.nome}</div>
        <div class="popup-address">📍 ${church.bairro}</div>
        ${church.telefone ? `<div class="popup-times">📞 ${church.telefone}</div>` : ''}
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
          <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${isOpen ? '#2D7A4F' : '#B5620A'}"></span>
          <span style="font-size:0.72rem;color:${isOpen ? '#2D7A4F' : '#B5620A'};font-weight:600;">
            ${isOpen ? 'Tem atividade no horário selecionado' : 'Sem atividade no horário selecionado'}
          </span>
        </div>
      `

      const btn = document.createElement('button')
      btn.className = 'popup-btn'
      btn.textContent = 'Ver horários completos'
      btn.onclick = () => {
        onSelectChurch(church)
        instanceRef.current.closePopup()
      }
      popupContent.appendChild(btn)

      marker.bindPopup(popupContent, { maxWidth: 240 })
      marker.addTo(instanceRef.current)
      markersRef.current[church.id] = marker
    })
  }, [churches, filteredIds, onSelectChurch])

  return <div ref={mapRef} className="map-container" style={{ height: '500px' }} />
}
