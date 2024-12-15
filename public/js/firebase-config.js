// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyA1c87i1EGMMuQEuptY7xKUUarl7ASfTAU",
  authDomain: "invoice-processor-app.firebaseapp.com",
  projectId: "invoice-processor-app",
  storageBucket: "invoice-processor-app.firebasestorage.app",
  messagingSenderId: "663459887541",
  appId: "1:663459887541:web:02483ee4cd0cbf19ef41fc",
  measurementId: "G-G6FRPF3DSH",
};

// Initialize Firebase with error handling
try {
  firebase.initializeApp(firebaseConfig);
  console.log("Firebase initialized successfully");

  // Initialize Firebase features
  const analytics = firebase.analytics();
  const storage = firebase.storage();

  // Test storage connection
  storage
    .ref()
    .child("test.txt")
    .putString("test")
    .then(() => {
      console.log("Storage connection successful");
      // Clean up test file
      storage.ref().child("test.txt").delete();
    })
    .catch((error) => {
      console.error("Storage connection failed:", error);
    });
} catch (error) {
  console.error("Error initializing Firebase:", error);
}
