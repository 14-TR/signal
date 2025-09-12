export default function SubscribeForm() {
  return (
    <form action="https://app.convertkit.com/forms/FORM_ID/subscriptions" method="post">
      <input type="email" name="email_address" placeholder="Your email" required />
      <button type="submit">Subscribe</button>
    </form>
  );
}
