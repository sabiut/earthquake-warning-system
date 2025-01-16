const EarthquakeTimeSeries = ({ predictions }) => {
    const timeSeriesData = predictions.map(p => ({
        date: new Date(p.time).toLocaleDateString(),
        magnitude: p.magnitude,
        place: p.place
    }));

    return React.createElement('div', { className: 'bg-white p-6 rounded-lg shadow-lg' },
        React.createElement('h2', { className: 'text-xl font-semibold mb-4' },
            'Predicted Earthquake Magnitudes Over Time'
        ),
        React.createElement('div', { className: 'h-64' },
            React.createElement(Recharts.ResponsiveContainer, { width: '100%', height: '100%' },
                React.createElement(Recharts.LineChart, { data: timeSeriesData },
                    React.createElement(Recharts.CartesianGrid, { strokeDasharray: '3 3' }),
                    React.createElement(Recharts.XAxis, { dataKey: 'date' }),
                    React.createElement(Recharts.YAxis, { domain: [3.5, 3.6] }),
                    React.createElement(Recharts.Tooltip, {
                        content: ({ active, payload, label }) => {
                            if (active && payload && payload.length) {
                                return React.createElement('div', 
                                    { className: 'bg-white p-4 border rounded shadow' },
                                    React.createElement('p', {}, `Date: ${label}`),
                                    React.createElement('p', {}, `Magnitude: ${payload[0].value.toFixed(3)}`),
                                    React.createElement('p', {}, `Location: ${timeSeriesData.find(d => d.date === label)?.place}`)
                                );
                            }
                            return null;
                        }
                    }),
                    React.createElement(Recharts.Line, {
                        type: 'monotone',
                        dataKey: 'magnitude',
                        stroke: '#2563eb',
                        dot: { r: 4 },
                        activeDot: { r: 8 }
                    })
                )
            )
        )
    );
};