/**
 * Travel Planner Engine — script.js
 * Handles form submission, API calls, and dynamic UI rendering.
 */

'use strict';

// ─── DOM References ──────────────────────────────────────────────────────────
const form        = document.getElementById('trip-form');
const loadingEl   = document.getElementById('loading');
const loadingDest = document.getElementById('loading-dest');
const resultsEl   = document.getElementById('results');
const errorBanner = document.getElementById('error-banner');
const errorMsg    = document.getElementById('error-msg');
const mapSection  = document.getElementById('map-section');
const mapDiv      = document.getElementById('destination-map');

// ─── State ───────────────────────────────────────────────────────────────────
let currentPlan = null;

// ─── Init ─────────────────────────────────────────────────────────────────────
// No init tasks required (no database).

// ─── Form Submission ─────────────────────────────────────────────────────────
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  await planTrip();
});

async function planTrip() {
  const destination = document.getElementById('destination').value.trim();
  const days        = parseInt(document.getElementById('days').value, 10);
  const budget      = parseFloat(document.getElementById('budget').value);
  const travelers   = parseInt(document.getElementById('travelers').value, 10);
  const interests   = getSelectedInterests();

  if (!destination || isNaN(days) || isNaN(budget) || isNaN(travelers)) {
    showError('Please fill in all required fields.');
    return;
  }
  if (interests.length === 0) {
    showError('Please select at least one interest.');
    return;
  }

  setLoading(true, destination);
  hideError();
  hideResults();

  try {
    const response = await fetch('/api/plan-trip', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ destination, days, budget, travelers, interests }),
    });

    const data = await response.json();

    if (window.gtag) {
      gtag('event', 'generate_trip_plan', {
        'event_category': 'Trip Planning',
        'event_label': destination,
        'value': budget
      });
    }

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to generate trip plan.');
    }

    currentPlan = data;
    renderResults(data);

    // Smooth scroll to results
    resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (err) {
    showError(err.message || 'An unexpected error occurred. Please try again.');
  } finally {
    setLoading(false);
  }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
function getSelectedInterests() {
  return [...document.querySelectorAll('.interest-chip input:checked')]
    .map(cb => cb.value);
}

function setLoading(active, dest = '') {
  if (active) {
    loadingDest.textContent = dest;
    loadingEl.classList.add('active');
    form.querySelector('button[type="submit"]').disabled = true;
  } else {
    loadingEl.classList.remove('active');
    form.querySelector('button[type="submit"]').disabled = false;
  }
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorBanner.classList.add('active');
}
function hideError()   { errorBanner.classList.remove('active'); }
function hideResults() { resultsEl.classList.remove('active'); }

function fmt(num) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(num);
}
function esc(str) {
  const d = document.createElement('div');
  d.textContent = str ?? '';
  return d.innerHTML;
}

// ─── Rendering ────────────────────────────────────────────────────────────────
function renderResults(plan) {
  const root = document.getElementById('results-inner');
  root.innerHTML = '';

  root.appendChild(renderTripBanner(plan));
  root.appendChild(renderWeather(plan.weather_info));
  root.appendChild(renderBudget(plan.budget_breakdown));
  root.appendChild(renderItinerary(plan.itinerary));
  root.appendChild(renderAttractions(plan.attractions));
  root.appendChild(renderFood(plan.food_suggestions));
  root.appendChild(renderHiddenGems(plan.hidden_gems));
  root.appendChild(renderTips(plan.travel_tips));

  if (plan.nearby_places && plan.nearby_places.length) {
    root.appendChild(renderNearby(plan.nearby_places));
  }

  // Initialize Map if Google Maps API is loaded
  if (window._mapsReady && plan.nearby_places && plan.nearby_places.length > 0) {
      initDestinationMap(plan);
  } else {
      mapSection.classList.add('hidden');
  }

  resultsEl.classList.add('active');
}

function initDestinationMap(plan) {
    mapSection.classList.remove('hidden');
    // Use the first nearby place to center the map, as we don't have explicit lat/lng for the destination itself in the schema
    const firstPlace = plan.nearby_places[0];
    const center = { lat: firstPlace.lat, lng: firstPlace.lng };

    const map = new google.maps.Map(mapDiv, {
        zoom: 12,
        center: center,
        mapId: 'DEMO_MAP_ID', // Replace with a real Map ID if using advanced markers
    });

    // Add marker for destination center
    new google.maps.Marker({
        position: center,
        map: map,
        title: plan.destination,
        icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
    });

    // Add markers for nearby places
    plan.nearby_places.forEach(place => {
        if (place.lat && place.lng) {
            const marker = new google.maps.Marker({
                position: { lat: place.lat, lng: place.lng },
                map: map,
                title: place.name
            });
            const infoWindow = new google.maps.InfoWindow({
                content: `<div style="padding: 5px;"><strong>${esc(place.name)}</strong><br>${esc(place.address)}</div>`
            });
            marker.addListener("click", () => {
                infoWindow.open({
                    anchor: marker,
                    map,
                });
            });
        }
    });
}

function sectionWrap(iconEmoji, iconColor, title, subtitle, content) {
  const section = document.createElement('section');
  section.className = 'fade-in mb-4';
  section.innerHTML = `
    <div class="section-header">
      <div class="section-icon" style="background:${iconColor}20">${iconEmoji}</div>
      <div>
        <div class="section-title">${esc(title)}</div>
        <div class="section-subtitle">${esc(subtitle)}</div>
      </div>
    </div>`;
  section.appendChild(content);
  return section;
}

// Trip Banner
function renderTripBanner(plan) {
  const interests = (plan.interests || []).map(i => `<span class="pill">🏷 ${esc(i)}</span>`).join('');
  const div = document.createElement('div');
  div.className = 'trip-banner fade-in';
  div.innerHTML = `
    <div class="trip-banner-info">
      <h2>✈️ ${esc(plan.destination)}</h2>
      <p>Your personalized AI-crafted travel experience is ready!</p>
      <div class="trip-meta-pills">
        <span class="pill">📅 ${plan.days} day${plan.days > 1 ? 's' : ''}</span>
        <span class="pill">💰 ${fmt(plan.budget)} total</span>
        <span class="pill">👥 ${plan.travelers} traveler${plan.travelers > 1 ? 's' : ''}</span>
        ${interests}
      </div>
    </div>`;
  return div;
}

// Weather
function renderWeather(weather) {
  const container = document.createElement('div');
  if (!weather) {
    container.className = 'hidden';
    return container;
  }
  const packing = (weather.packing_suggestions || [])
    .map(p => `<li>${esc(p)}</li>`).join('');

  const weatherIcons = { 'Clear': '☀️', 'cloud': '⛅', 'Rain': '🌧️', 'Snow': '❄️', 'Thunder': '⛈️', 'Fog': '🌫️' };
  let icon = '🌤️';
  for (const [key, val] of Object.entries(weatherIcons)) {
    if (weather.condition?.includes(key)) { icon = val; break; }
  }

  container.className = 'weather-card fade-in mb-4';
  container.innerHTML = `
    <div class="weather-main">
      <div class="weather-icon">${icon}</div>
      <div class="weather-temp">${esc(weather.temperature_range)}</div>
      <div class="weather-cond">${esc(weather.condition)}</div>
      <div class="weather-best">🕐 Best time: ${esc(weather.best_time)}</div>
    </div>
    <div class="weather-packing">
      <div class="packing-title">🎒 What to Pack</div>
      <ul class="packing-list">${packing}</ul>
    </div>`;
  return container;
}

// Budget
function renderBudget(budget) {
  if (!budget) return document.createElement('div');
  const categories = [
    { key: 'accommodation',  label: 'Accommodation', icon: '🏨' },
    { key: 'food',           label: 'Food & Dining',  icon: '🍽️' },
    { key: 'transportation', label: 'Transport',      icon: '🚌' },
    { key: 'activities',     label: 'Activities',     icon: '🎭' },
    { key: 'shopping',       label: 'Shopping',       icon: '🛍️' },
    { key: 'emergency',      label: 'Emergency',      icon: '🆘' },
  ];

  const grid = document.createElement('div');
  grid.className = 'budget-grid';
  categories.forEach(c => {
    grid.innerHTML += `
      <div class="budget-card">
        <div class="budget-icon">${c.icon}</div>
        <div class="budget-label">${c.label}</div>
        <div class="budget-amount">${fmt(budget[c.key] ?? 0)}</div>
      </div>`;
  });
  grid.innerHTML += `
    <div class="budget-card total-card">
      <div class="budget-icon">💎</div>
      <div class="budget-label">Per Person</div>
      <div class="budget-amount">${fmt(budget.per_person ?? 0)}</div>
    </div>`;

  return sectionWrap('💰', '#f59e0b', 'Budget Breakdown', `Total: ${fmt(budget.total ?? 0)} · Style: ${budget.style ?? 'mid'}-range`, grid);
}

// Itinerary
function renderItinerary(itinerary) {
  if (!itinerary?.length) return document.createElement('div');
  const container = document.createElement('div');
  container.className = 'itinerary-days';

  itinerary.forEach((day, idx) => {
    const activities = (day.activities || []).map(a => `
      <div class="activity-item">
        <div class="activity-time">${esc(a.time)}</div>
        <div class="activity-content">
          <div class="activity-name">${esc(a.activity)}</div>
          <div class="activity-location">📍 ${esc(a.location)}</div>
          ${a.estimated_cost > 0 ? `<span class="activity-cost">~${fmt(a.estimated_cost)}</span>` : ''}
          ${a.tips ? `<div class="activity-tip">💡 ${esc(a.tips)}</div>` : ''}
        </div>
      </div>`).join('');

    const meals = (day.meals || []).map(m => `<div class="meal-item">🍴 ${esc(m)}</div>`).join('');

    const card = document.createElement('div');
    card.className = 'day-card' + (idx === 0 ? ' open' : '');
    card.innerHTML = `
      <div class="day-header" role="button" aria-expanded="${idx === 0}" tabindex="0">
        <div>
          <div class="day-num">Day ${day.day}</div>
          <div class="day-theme">${esc(day.theme)}</div>
        </div>
        <div class="day-toggle">▾</div>
      </div>
      <div class="day-body">
        <div class="activity-list">${activities}</div>
        ${meals ? `<div class="day-meals"><div class="meals-title">🍽️ Meal Plan</div>${meals}</div>` : ''}
      </div>`;

    card.querySelector('.day-header').addEventListener('click', () => {
      card.classList.toggle('open');
    });
    card.querySelector('.day-header').addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); card.classList.toggle('open'); }
    });
    container.appendChild(card);
  });

  return sectionWrap('🗓️', '#6366f1', 'Day-by-Day Itinerary', `${itinerary.length} days of curated experiences`, container);
}

// Attractions
function renderAttractions(attractions) {
  if (!attractions?.length) return document.createElement('div');
  const grid = document.createElement('div');
  grid.className = 'cards-grid';
  attractions.forEach(a => {
    const stars = a.rating ? '★'.repeat(Math.round(a.rating)) + `(${a.rating})` : '';
    grid.innerHTML += `
      <div class="info-card">
        <div class="card-category">${esc(a.category)}</div>
        <div class="card-name">${esc(a.name)}</div>
        <div class="card-desc">${esc(a.description)}</div>
        ${stars ? `<div class="card-rating">⭐ ${esc(stars)}</div>` : ''}
        ${a.estimated_cost != null ? `<div class="card-price">💵 ~${fmt(a.estimated_cost)}</div>` : ''}
      </div>`;
  });
  return sectionWrap('🗺️', '#8b5cf6', 'Top Attractions', 'Must-visit places curated by AI', grid);
}

// Food
function renderFood(food) {
  if (!food?.length) return document.createElement('div');
  const grid = document.createElement('div');
  grid.className = 'cards-grid';
  food.forEach(f => {
    grid.innerHTML += `
      <div class="info-card">
        <div class="card-category">${esc(f.cuisine_type)}</div>
        <div class="card-name">${esc(f.name)}</div>
        <div class="card-desc">${esc(f.description)}</div>
        <div class="card-price">💰 ${esc(f.price_range)}</div>
        ${f.must_try ? `<div class="card-highlight">🌟 ${esc(f.must_try)}</div>` : ''}
      </div>`;
  });
  return sectionWrap('🍜', '#f59e0b', 'Local Food & Dining', 'Authentic flavors you must try', grid);
}

// Hidden Gems
function renderHiddenGems(gems) {
  if (!gems?.length) return document.createElement('div');
  const grid = document.createElement('div');
  grid.className = 'cards-grid';
  gems.forEach(g => {
    grid.innerHTML += `
      <div class="info-card">
        <div class="card-category">Hidden Gem</div>
        <div class="card-name">💎 ${esc(g.name)}</div>
        <div class="card-desc">${esc(g.description)}</div>
        <div class="card-highlight">✨ ${esc(g.why_special)}</div>
        ${g.best_time_to_visit ? `<div class="card-price">🕐 Best: ${esc(g.best_time_to_visit)}</div>` : ''}
      </div>`;
  });
  return sectionWrap('💎', '#10b981', 'Hidden Gems', 'Off-the-beaten-path discoveries', grid);
}

// Travel Tips
function renderTips(tips) {
  if (!tips?.length) return document.createElement('div');
  const list = document.createElement('div');
  list.className = 'tips-list';
  tips.forEach((tip, i) => {
    list.innerHTML += `
      <div class="tip-item">
        <div class="tip-num">${i + 1}</div>
        <div class="tip-text">${esc(tip)}</div>
      </div>`;
  });
  return sectionWrap('💡', '#38bdf8', 'Travel Tips', 'Expert advice for a smooth journey', list);
}

// Nearby Places
function renderNearby(places) {
  const grid = document.createElement('div');
  grid.className = 'nearby-grid';
  places.slice(0, 8).forEach(p => {
    const imgHtml = p.photo_url
      ? `<img src="${esc(p.photo_url)}" alt="${esc(p.name)}" loading="lazy" />`
      : `<span>📍</span>`;
    const types = (p.types || []).slice(0, 2).map(t => t.replace(/_/g, ' ')).join(', ');
    grid.innerHTML += `
      <div class="nearby-card">
        <div class="nearby-card-img">${imgHtml}</div>
        <div class="nearby-card-body">
          <div class="nearby-card-name">${esc(p.name)}</div>
          <div class="nearby-card-addr">${esc(p.address)}</div>
          <div class="nearby-card-meta">
            ${p.rating ? `<span class="nearby-rating">⭐ ${p.rating}</span>` : ''}
            <span class="nearby-type">${esc(types)}</span>
          </div>
        </div>
      </div>`;
  });
  return sectionWrap('📍', '#f43f5e', 'Nearby Places', 'Real data from Google Maps', grid);
}

