"""Streamlit UI for Vietnamese news summarization inference.

Provides two modes:
1. Paste article text manually for summarization.
2. Crawl today's RSS feeds and summarize automatically.
"""

from __future__ import annotations

import asyncio
import os

import streamlit as st

st.set_page_config(
    page_title="VN News Summarizer",
    page_icon="📰",
    layout="wide",
)


@st.cache_resource(show_spinner="Đang tải model ViT5...")
def load_summarizer():
    from app.summarizer import ViT5Summarizer

    return ViT5Summarizer()


def main() -> None:
    st.title("📰 VN News Summarizer")
    st.caption("Tóm tắt tin tức tiếng Việt bằng mô hình ViT5 fine-tuned với LoRA.")

    summarizer = load_summarizer()
    st.sidebar.header("Thông tin model")
    st.sidebar.text(f"Model: {summarizer.model_id}")
    st.sidebar.text(f"Max input: {summarizer.generation.max_input_length}")
    st.sidebar.text(f"Max output: {summarizer.generation.max_new_tokens}")
    st.sidebar.text(f"Beam search: {summarizer.generation.num_beams}")

    tab_manual, tab_crawl = st.tabs(["✍️ Nhập văn bản", "🌐 Crawl tin mới"])

    with tab_manual:
        st.subheader("Tóm tắt văn bản thủ công")
        st.markdown("Dán nội dung bài báo tiếng Việt vào ô bên dưới, nhấn **Tóm tắt**.")

        input_text = st.text_area(
            "Nội dung bài báo",
            height=300,
            placeholder="Dán nội dung bài báo tiếng Việt vào đây...",
        )

        if st.button("Tóm tắt", key="btn_manual", type="primary"):
            if not input_text or not input_text.strip():
                st.warning("Vui lòng nhập nội dung bài báo.")
            else:
                with st.spinner("Đang tóm tắt..."):
                    summary = summarizer.summarize(input_text)
                st.success("Kết quả tóm tắt:")
                st.info(summary)

    with tab_crawl:
        st.subheader("Crawl và tóm tắt tin tức hôm nay")
        st.markdown(
            "Crawl tin mới nhất từ các nguồn RSS (VnExpress, Tuổi Trẻ, Thanh Niên, ...) "
            "rồi tóm tắt bằng model ViT5."
        )

        limit = st.slider(
            "Số bài tối đa",
            min_value=1,
            max_value=20,
            value=int(os.environ.get("MAX_ARTICLES_PER_DEMO", "5")),
        )

        if st.button("Crawl & Tóm tắt", key="btn_crawl", type="primary"):
            from app.crawler import crawl_articles

            with st.spinner("Đang crawl tin tức từ RSS..."):
                articles, _stats = asyncio.run(
                    crawl_articles(mode="demo", limit=limit)
                )

            if not articles:
                st.error("Không crawl được bài nào. Vui lòng thử lại sau.")
            else:
                with st.spinner(f"Đang tóm tắt {len(articles)} bài..."):
                    summaries = summarizer.summarize_batch(
                        [a.content_text for a in articles]
                    )

                st.success(f"Đã tóm tắt {len(articles)} bài!")

                for article, summary in zip(articles, summaries, strict=True):
                    with st.container():
                        st.markdown(f"### [{article.title}]({article.url})")
                        st.caption(
                            f"📌 {article.source_name}"
                            + (f" — {article.published_at}" if article.published_at else "")
                        )
                        st.info(summary)
                        st.divider()


if __name__ == "__main__":
    main()
