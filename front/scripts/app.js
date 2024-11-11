document.addEventListener("DOMContentLoaded", () => {
  const video = document.getElementById("video");
  const captureBtn = document.getElementById("capture-btn");
  const gallery = document.getElementById("gallery");

  
  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      video.srcObject = stream;
    } catch (error) {
      console.error("Error accessing camera:", error);
    }
  }

  async function captureFrame() {
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(async (blob) => {
      const formData = new FormData();
      const uniqueFilename = `captured_frame_${Date.now()}.png`; // Unique filename using timestamp
      formData.append('image', blob, uniqueFilename);
      console.log("Blob size:", blob.size)

      try {
        const response = await fetch('http://localhost:5000/upload-image', {
          method: 'POST',
          body: formData
        });

        const result = await response.json();
        if (response.ok) {
          console.log('Extracted Text:', result.text);
          console.log('Server response:', result)
          alert('Text extracted: ' + result.text);
        } else {
          console.error('Error:', result.error);
          alert('Error: ' + result.error);
        }
      } catch (error) {
        console.error('Error uploading image:', error);
      }
    }, 'image/png');
  }

  captureBtn.addEventListener("click", captureFrame);
  startCamera();
});
