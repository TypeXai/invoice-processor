// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: process.env.FIREBASE_API_KEY || "YOUR_API_KEY",
  authDomain:
    process.env.FIREBASE_AUTH_DOMAIN || "invoice-processor-app.firebaseapp.com",
  projectId: process.env.FIREBASE_PROJECT_ID || "invoice-processor-app",
  storageBucket:
    process.env.FIREBASE_STORAGE_BUCKET ||
    "invoice-processor-app.firebasestorage.app",
  messagingSenderId: process.env.FIREBASE_SENDER_ID || "YOUR_SENDER_ID",
  appId: process.env.FIREBASE_APP_ID || "YOUR_APP_ID",
  measurementId: process.env.FIREBASE_MEASUREMENT_ID || "YOUR_MEASUREMENT_ID",
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
