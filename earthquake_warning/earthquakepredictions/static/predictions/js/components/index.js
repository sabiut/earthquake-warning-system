const PredictionsVisualization = ({ data }) => {
    return React.createElement('div', { className: 'space-y-6' },
        React.createElement(EarthquakeTimeSeries, { predictions: data.predictions }),
        React.createElement(EarthquakeMap, { predictions: data.predictions })
    );
};