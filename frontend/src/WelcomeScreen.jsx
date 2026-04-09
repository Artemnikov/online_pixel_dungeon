const WelcomeScreen = ({ onStart }) => {
  return (
    <div className="welcome-screen">
      <h1 className="welcome-title">Welcome to<br />Online Pixel Dungeon</h1>
      <button className="welcome-btn" onClick={onStart}>
        Start your journey
      </button>

      <style jsx>{`
        .welcome-screen {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100vh;
          background-color: #111;
          color: white;
          font-family: monospace;
          gap: 40px;
        }
        .welcome-title {
          font-size: 42px;
          text-align: center;
          color: #f1c40f;
          text-shadow: 0 0 20px rgba(241, 196, 15, 0.4);
          line-height: 1.4;
          margin: 0;
        }
        .welcome-btn {
          font-size: 22px;
          padding: 15px 45px;
          background-color: #27ae60;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-family: monospace;
        }
        .welcome-btn:hover {
          background-color: #2ecc71;
        }
      `}</style>
    </div>
  );
};

export default WelcomeScreen;
