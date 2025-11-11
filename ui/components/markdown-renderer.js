const { Typography } = antd;

function MarkdownRenderer({ content }) {
    const htmlContent = React.useMemo(function() {
        if (!content) return '';
        return marked.parse(content);
    }, [content]);

    return React.createElement('div', {
        className: 'markdown-content',
        dangerouslySetInnerHTML: { __html: htmlContent },
        style: {
            lineHeight: '1.6',
            wordBreak: 'break-word'
        }
    });
}
