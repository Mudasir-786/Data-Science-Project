# Frontend folder structure documentation

This folder contains all frontend assets for the AQI Monitoring System.

## Structure

```
frontend/
├── templates/          # HTML Jinja2 templates
│   ├── index_advanced.html       # Main dashboard
│   ├── compare.html              # 3-city comparison
│   ├── compare_advanced.html     # 5-city statistical comparison
│   ├── forecast.html             # 7-day AQI prediction
│   ├── analytics.html            # Statistical analysis
│   ├── heatmap.html              # Geographic visualization
│   ├── history.html              # Search history
│   ├── rankings.html             # City rankings
│   ├── calculator.html           # AQI calculator
│   └── test_features.html        # Feature testing
│
└── static/             # Static assets (CSS, JS, images)
    ├── css/            # Custom stylesheets
    └── js/             # JavaScript files
```

## Technologies Used

- **HTML5**: Semantic markup
- **Bootstrap 5**: Responsive CSS framework
- **Chart.js 3.x**: Data visualizations
- **JavaScript ES6**: Client-side interactivity
- **Jinja2**: Template engine (Flask integration)

## Template Features

All templates include:
- Responsive design (mobile, tablet, desktop)
- Dark mode support
- Bootstrap components
- Chart.js visualizations
- Autocomplete search
- Real-time data updates
