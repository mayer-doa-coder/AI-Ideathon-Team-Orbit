import { useState } from "react";
import { Link } from "react-router-dom";
import { checkout, getPaymentHistory } from "../services/paymentApi";
import { useAuth } from "../context/AuthContext";
import "../styles/payment.css";

const PLANS = [
  { id: "season-report", label: "Premium Season Report", amount: 5, description: "AgriSense Premium Season Report" },
  { id: "crop-diagnosis", label: "Priority Crop Diagnosis", amount: 10, description: "AgriSense Priority Crop Diagnosis" },
  { id: "monthly", label: "Monthly Advisory Pass", amount: 49, description: "AgriSense Monthly Advisory Pass" },
];

export default function PaymentPage() {
  const { token } = useAuth();
  const [msisdn, setMsisdn] = useState("");
  const [planId, setPlanId] = useState(PLANS[0].id);
  const [isPaying, setIsPaying] = useState(false);
  const [receipt, setReceipt] = useState(null);
  const [error, setError] = useState("");
  const [history, setHistory] = useState(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const plan = PLANS.find((p) => p.id === planId);

  async function handleCheckout(e) {
    e.preventDefault();
    if (!msisdn.trim()) return;

    setError("");
    setReceipt(null);
    setIsPaying(true);
    try {
      const result = await checkout(token, {
        msisdn: msisdn.trim(),
        amount: plan.amount,
        description: plan.description,
      });
      setReceipt(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsPaying(false);
    }
  }

  async function handleShowHistory() {
    if (!msisdn.trim()) return;
    setIsLoadingHistory(true);
    try {
      const rows = await getPaymentHistory(token, msisdn.trim());
      setHistory(rows);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoadingHistory(false);
    }
  }

  return (
    <div className="payment-page">
      <div className="payment-card">
        <Link to="/chat" className="payment-back-link">
          &larr; Back to dashboard
        </Link>
        <h1>AgriSense Premium</h1>
        <p className="payment-subtitle">
          Pay directly from your mobile operator balance via BDApps CaaS — no card, no bank account
          needed. A successful payment unlocks one-to-one Expert Consultancy with crop specialists.
        </p>

        <form onSubmit={handleCheckout} className="payment-form">
          <label className="payment-label" htmlFor="msisdn">
            Phone number
          </label>
          <input
            id="msisdn"
            type="tel"
            placeholder="e.g. 01605012802"
            value={msisdn}
            onChange={(e) => setMsisdn(e.target.value)}
            required
          />

          <label className="payment-label">Choose a plan</label>
          <div className="payment-plans">
            {PLANS.map((p) => (
              <label key={p.id} className={`payment-plan ${planId === p.id ? "payment-plan-selected" : ""}`}>
                <input
                  type="radio"
                  name="plan"
                  value={p.id}
                  checked={planId === p.id}
                  onChange={() => setPlanId(p.id)}
                />
                <span className="payment-plan-label">{p.label}</span>
                <span className="payment-plan-amount">৳{p.amount}</span>
              </label>
            ))}
          </div>

          <button type="submit" disabled={isPaying}>
            {isPaying ? "Processing..." : `Pay ৳${plan.amount} now`}
          </button>
        </form>

        {error && <div className="payment-error">{error}</div>}

        {receipt && receipt.success && (
          <div className="payment-unlock-banner">
            <div>
              <strong>Expert consultancy unlocked</strong>
              <span>You can now ask crop experts for personalised guidance.</span>
            </div>
            <Link to="/consultancy" className="payment-unlock-btn">
              Talk to a crop expert
            </Link>
          </div>
        )}

        {receipt && (
          <div className={`payment-receipt ${receipt.success ? "payment-receipt-success" : "payment-receipt-failed"}`}>
            <h2>{receipt.success ? "Payment successful" : "Payment failed"}</h2>
            <dl>
              <dt>Transaction ID</dt>
              <dd>{receipt.external_trx_id}</dd>
              <dt>Phone number</dt>
              <dd>{receipt.msisdn}</dd>
              <dt>Amount</dt>
              <dd>৳{receipt.amount} {receipt.currency}</dd>
              <dt>Description</dt>
              <dd>{receipt.description}</dd>
              <dt>BDApps status</dt>
              <dd>{receipt.status_code} — {receipt.status_detail}</dd>
              <dt>Time</dt>
              <dd>{new Date(receipt.created_at).toLocaleString()}</dd>
            </dl>
          </div>
        )}

        <div className="payment-history-section">
          <button type="button" className="payment-history-toggle" onClick={handleShowHistory} disabled={isLoadingHistory}>
            {isLoadingHistory ? "Loading..." : "View past transactions for this number"}
          </button>

          {history && history.length === 0 && <p className="payment-history-empty">No past transactions.</p>}

          {history && history.length > 0 && (
            <table className="payment-history-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th>Amount</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {history.map((row) => (
                  <tr key={row.transaction_id}>
                    <td>{new Date(row.created_at).toLocaleDateString()}</td>
                    <td>{row.description}</td>
                    <td>৳{row.amount}</td>
                    <td className={row.success ? "payment-status-ok" : "payment-status-fail"}>
                      {row.success ? "Success" : "Failed"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
