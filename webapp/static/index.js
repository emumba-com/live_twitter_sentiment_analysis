google.charts.load('current', {'packages':['annotationchart']})

var timeline_data
var chart
var options = {
    displayAnnotations: true
}

function drawChart() {
    timeline_data = new google.visualization.DataTable()
    timeline_data.addColumn('datetime', 'Date')
    timeline_data.addColumn('number', 'Sentiment')
    chart = new google.visualization.AnnotationChart(document.getElementById('chart_div'))
    chart.draw(timeline_data, options)
}

google.charts.setOnLoadCallback(drawChart)

var socket = io('http://localhost:8001')
socket.on('connect', function(){
    console.log('socket io connected')
})

socket.on('disconnect', function(){
    console.log('socket io disconnected')
})

// whenever averaged sentiment is received from twitter, append data
// and redraw chart
socket.on('event', function(data){
    timeline_data.addRows([[new Date(), parseFloat(data)]])
    chart = new google.visualization.AnnotationChart(document.getElementById('chart_div'))
    chart.draw(data, options)
    chart.draw(timeline_data, options)
})

