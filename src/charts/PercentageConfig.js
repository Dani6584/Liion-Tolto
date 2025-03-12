export const data = {
  labels: [],
  datasets: [
    {
      data: [100],
      borderWidth: 5,
      borderColor: ['#ffffff'],
      backgroundColor: ['#e74c3c']
    }
  ]
}

export const options = {
  responsive: true,
  maintainAspectRatio: false,
  rotation: -90,
  circumference: 180,
  plugins: {
      legend:  { display: false },
      tooltip: { enabled: false }
  }
}