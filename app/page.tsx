import SubscribeForm from "../components/SubscribeForm";
import ArticleList from "../components/ArticleList";

export default function Page() {
  return (
    <main>
      <h1>Signal.ai Newsletter</h1>
      <SubscribeForm />
      <ArticleList />
    </main>
  );
}
