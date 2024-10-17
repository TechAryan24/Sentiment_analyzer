

// Update the chart's gradient based on values
let positivePercent = (positive / total) * 100;
let neutralPercent = (neutral / total) * 100;
let negativePercent = (negative / total) * 100;

// Update the chart's background
document.querySelector('.chart').style.background = 
    `conic-gradient(
        #4CAF50 0 ${positivePercent}%,
        gray ${positivePercent}% ${positivePercent + neutralPercent}%,
        red ${positivePercent + neutralPercent}% 100%
    )`;

// Optionally update the chart text with the dominant sentiment
let dominant = Math.max(positive, neutral, negative);
let dominantSentiment = dominant === positive ? 'Positive'
                    : dominant === neutral ? 'Neutral'
                    : 'Negative';
document.getElementById('percentage').innerText = `${dominantSentiment}: ${dominant}`;

}

// // Add event listeners to the chart colors
// document.querySelectorAll('.chart-description div').forEach((element) => {
//     element.addEventListener('mouseover', () => {
//         const sentiment = element.classList[0];
//         const percentage = document.getElementById(${sentiment}-percentage).innerText;
//         alert(${sentiment} comments: ${percentage});
//     });
// });
