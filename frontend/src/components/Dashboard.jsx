import { useEffect, useState } from "react";
import { api } from "../api/client";
import UploadCSV from "./UploadCSV";
import SpendingChart from "./SpendingChart";
import InsightsPanel from "./InsightsPanel";
import TransactionTable from "./TransactionTable";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [transactions, setTransactions] = useState([]);

  const loadData = async () => {
    const [s, t] = await Promise.all([
      api.get("/transactions/stats"),
      api.get("/transactions/?per_page=20"),
    ]);
    setStats(s);
    setTransactions(t.transactions);
  };

  useEffect(() => { loadData(); }, []);

  return (
    <div className="dashboard">
      <header>
        <h1>💰 Finance Dashboard</h1>
        <button onClick={() => { localStorage.removeItem("token"); window.location.reload(); }}>
          Logout
        </button>
      </header>

      <UploadCSV onUploaded={loadData} />

      {stats && (
        <div className="stats-row">
          <div className="stat-card">
            <span>Total Income</span>
            <strong>₹{stats.total_income.toLocaleString()}</strong>
          </div>
          <div className="stat-card">
            <span>Total Spent</span>
            <strong>₹{stats.total_spent.toLocaleString()}</strong>
          </div>
          <div className="stat-card">
            <span>Transactions</span>
            <strong>{stats.transaction_count}</strong>
          </div>
        </div>
      )}

      <div className="grid-2">
        {stats && <SpendingChart byCategory={stats.by_category} />}
        <InsightsPanel />
      </div>

      <TransactionTable transactions={transactions} />
    </div>
  );
}