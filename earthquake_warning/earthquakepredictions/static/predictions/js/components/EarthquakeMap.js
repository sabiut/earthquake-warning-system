const EarthquakeMap = ({ predictions }) => {
    const minLat = Math.min(...predictions.map(p => p.latitude));
    const maxLat = Math.max(...predictions.map(p => p.latitude));
    const minLong = Math.min(...predictions.map(p => p.longitude));
    const maxLong = Math.max(...predictions.map(p => p.longitude));

    return React.createElement('div', { className: 'bg-white p-6 rounded-lg shadow-lg' },
        React.createElement('h2', { className: 'text-xl font-semibold mb-4' },
            'Geographic Distribution of Predicted Earthquakes'
        ),
        React.createElement('div', { className: 'h-64 relative' },
            React.createElement('svg', {
                viewBox: `${minLong - 0.5} ${minLat - 0.5} ${maxLong - minLong + 1} ${maxLat - minLat + 1}`,
                className: 'w-full h-full'
            },
                predictions.map((p, i) =>
                    React.createElement('g', { key: p.id },
                        React.createElement('circle', {
                            cx: p.longitude,
                            cy: p.latitude,
                            r: '0.05',
                            fill: '#2563eb',
                            opacity: '0.6'
                        }),
                        i % 3 === 0 && React.createElement('text', {
                            x: p.longitude + 0.1,
                            y: p.latitude,
                            fontSize: '0.2',
                            fill: '#4b5563'
                        }, p.place)
                    )
                )
            )
        )
    );
};