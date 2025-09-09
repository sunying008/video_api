"""
文本后处理模块 - 为转录文本添加标点符号和格式化
"""
import re
import logging
from typing import List, Optional, Dict


logger = logging.getLogger(__name__)


class TextPostProcessor:
    """文本后处理器"""
    
    def __init__(self):
        """初始化文本后处理器"""
        self.sentence_indicators = [
            # 中文语句结束指示词
            '吧', '呢', '啊', '哦', '嗯', '唉', '哎', '咦', '哇',
            '的话', '这样', '那样', '就是', '然后', '所以', '因为',
            '但是', '不过', '虽然', '如果', '要是', '除非',
            # 英文语句结束指示词
            'yeah', 'well', 'okay', 'right', 'actually', 'basically',
            'anyway', 'however', 'therefore', 'because', 'although'
        ]
        
        self.pause_indicators = [
            # 表示停顿的词语
            '嗯嗯', '啊啊', '呃', '额', '那个', '这个', '就是说',
            'um', 'uh', 'er', 'well', 'you know', 'I mean'
        ]
        
    def add_punctuation(self, text: str, language: str = 'auto') -> str:
        """
        为文本添加标点符号
        
        Args:
            text: 原始文本
            language: 语言类型 ('zh', 'en', 'auto')
            
        Returns:
            添加标点符号后的文本
        """
        if not text or not text.strip():
            return text
            
        # 检测语言（如果是auto）
        if language == 'auto':
            language = self._detect_language(text)
            
        logger.info(f"为文本添加标点符号，检测到语言: {language}")
        
        # 清理文本
        text = self._clean_text(text)
        
        # 分割成句子
        sentences = self._split_sentences_improved(text, language)
        
        # 为每个句子添加标点
        processed_sentences = []
        for sentence in sentences:
            if sentence.strip():
                processed_sentence = self._add_sentence_punctuation(sentence.strip(), language)
                if processed_sentence:
                    processed_sentences.append(processed_sentence)
        
        # 合并句子
        if language == 'zh':
            result = '\n'.join(processed_sentences)  # 每句一行，便于添加时间戳
        else:
            result = '\n'.join(processed_sentences)
                
        return result
    
    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        # 简单的语言检测：统计中文字符比例
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(re.sub(r'\s+', '', text))
        
        if total_chars == 0:
            return 'en'
            
        chinese_ratio = chinese_chars / total_chars
        return 'zh' if chinese_ratio > 0.3 else 'en'
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除重复的词语（如"就是就是"）
        text = re.sub(r'\b(\w+)\s+\1\b', r'\1', text)
        
        return text
    
    def _split_sentences(self, text: str, language: str) -> List[str]:
        """将文本分割成句子"""
        sentences = []
        
        if language == 'zh':
            # 中文分句 - 简化版本
            # 基于标点和关键词进行基本分句
            
            # 首先按已有标点分割
            parts = re.split(r'[。！？]', text)
            
            for part in parts:
                if not part.strip():
                    continue
                
                # 按语气词分割
                part = part.strip()
                sub_parts = []
                
                # 分割语气词
                words = part.split()
                current_sentence = []
                
                for word in words:
                    current_sentence.append(word)
                    
                    # 检查是否应该在此处分句
                    if (word.endswith(('吧', '呢', '啊', '哦')) or 
                        word in ['然后', '所以', '因为', '但是', '不过', '而且']):
                        if len(current_sentence) > 2:  # 确保句子有足够长度
                            sub_parts.append(' '.join(current_sentence))
                            current_sentence = []
                
                # 添加剩余的词
                if current_sentence:
                    sub_parts.append(' '.join(current_sentence))
                
                sentences.extend([s.strip() for s in sub_parts if len(s.strip()) > 5])
        
        else:
            # 英文分句 - 简化版本
            # 首先按已有标点分割
            parts = re.split(r'[.!?]', text)
            
            for part in parts:
                if not part.strip():
                    continue
                
                part = part.strip()
                sub_parts = []
                
                # 按连接词分割
                words = part.split()
                current_sentence = []
                
                for i, word in enumerate(words):
                    current_sentence.append(word)
                    
                    # 检查是否应该在此处分句
                    if (word.lower() in ['and', 'but', 'so', 'then', 'however', 'therefore', 
                                       'because', 'although', 'while', 'yeah', 'well', 'okay'] and
                        len(current_sentence) > 3):
                        sub_parts.append(' '.join(current_sentence[:-1]))  # 不包括连接词
                        current_sentence = [word]  # 从连接词开始新句子
                
                # 添加剩余的词
                if current_sentence:
                    sub_parts.append(' '.join(current_sentence))
                
                sentences.extend([s.strip() for s in sub_parts if len(s.strip()) > 5])
        
        return [s for s in sentences if len(s.strip()) > 3]
    
    def _split_sentences_improved(self, text: str, language: str) -> List[str]:
        """改进的分句方法"""
        if not text or not text.strip():
            return []
        
        # 预处理：清理文本
        text = re.sub(r'\s+', ' ', text.strip())
        
        if language == 'zh':
            return self._split_chinese_improved(text)
        else:
            return self._split_english_improved(text)
    
    def _split_chinese_improved(self, text: str) -> List[str]:
        """改进的中文分句"""
        sentences = []
        
        # 关键分句词
        split_words = ['然后', '接着', '后来', '于是', '所以', '因此', '但是', '不过', '而且', '另外', '首先', '其次', '再次', '最后', '总之', '此外']
        
        current_pos = 0
        
        while current_pos < len(text):
            # 查找下一个分句点
            next_split_pos = len(text)
            found_word = None
            
            for word in split_words:
                # 查找分句词的位置
                pos = text.find(word, current_pos)
                if pos > current_pos and pos < next_split_pos:
                    # 确保分句词前后有空格或在合适位置
                    if pos == 0 or text[pos-1] == ' ':
                        next_split_pos = pos
                        found_word = word
            
            if found_word:
                # 提取到分句词之前的内容
                sentence = text[current_pos:next_split_pos].strip()
                if sentence and len(sentence) > 6:
                    sentences.append(sentence)
                # 移动到分句词位置
                current_pos = next_split_pos
            else:
                # 没有找到更多分句词，处理剩余内容
                remaining = text[current_pos:].strip()
                if remaining and len(remaining) > 6:
                    sentences.append(remaining)
                break
        
        # 如果没有成功分句，尝试按长度强制分句
        if not sentences and text.strip():
            # 按逗号或较长的词组分句
            parts = re.split(r'[，,]', text)
            if len(parts) > 1:
                for part in parts:
                    if len(part.strip()) > 6:
                        sentences.append(part.strip())
            else:
                # 按长度强制分句
                chars = list(text)
                if len(chars) > 40:
                    mid = len(chars) // 2
                    # 寻找合适的分割点
                    for i in range(mid-5, mid+5):
                        if i < len(chars) and chars[i] == ' ':
                            sentences.append(text[:i].strip())
                            sentences.append(text[i:].strip())
                            break
                    else:
                        sentences.append(text.strip())
                else:
                    sentences.append(text.strip())
        
        return [s for s in sentences if s and len(s) > 6]
    
    def _split_english_improved(self, text: str) -> List[str]:
        """改进的英文分句"""
        sentences = []
        
        # 关键分句词
        split_words = ['then', 'next', 'after', 'so', 'therefore', 'but', 'however', 'and then', 'also', 'first', 'second', 'third', 'finally', 'lastly', 'meanwhile']
        
        # 转换为小写进行匹配
        text_lower = text.lower()
        
        current_pos = 0
        text_len = len(text)
        
        while current_pos < text_len:
            # 查找下一个分句点
            next_split = text_len
            split_word_found = None
            
            for word in split_words:
                # 使用正则表达式查找完整单词
                pattern = r'\b' + re.escape(word) + r'\b'
                match = re.search(pattern, text_lower[current_pos:])
                if match:
                    pos = current_pos + match.start()
                    if pos > current_pos and pos < next_split:
                        next_split = pos
                        split_word_found = word
            
            # 提取当前句子
            if split_word_found:
                sentence = text[current_pos:next_split].strip()
                if len(sentence.split()) > 4:  # 至少4个单词
                    sentences.append(sentence)
                current_pos = next_split
            else:
                # 没有找到分句词，取剩余全部内容
                sentence = text[current_pos:].strip()
                if len(sentence.split()) > 4:
                    sentences.append(sentence)
                break
        
        # 如果没有分句，按长度强制分句
        if not sentences and text.strip():
            words = text.split()
            if len(words) > 20:
                current_sentence = []
                for word in words:
                    current_sentence.append(word)
                    if len(current_sentence) > 15:
                        sentences.append(' '.join(current_sentence))
                        current_sentence = []
                if current_sentence:
                    sentences.append(' '.join(current_sentence))
            else:
                sentences.append(text.strip())
        
        return sentences
    
    def _preprocess_for_splitting(self, text: str, language: str) -> str:
        """预处理文本以便更好地分句"""
        if language == 'zh':
            # 在关键词前后添加分隔符
            markers = ['然后', '接着', '后来', '于是', '所以', '因此', '但是', '不过', '而且', '另外']
            for marker in markers:
                text = text.replace(f' {marker} ', f' | {marker} ')
                text = text.replace(f'{marker} ', f'| {marker} ')
        else:
            # 英文标记词
            markers = ['then', 'next', 'after', 'so', 'therefore', 'but', 'however', 'and', 'also']
            for marker in markers:
                text = text.replace(f' {marker} ', f' | {marker} ')
        
        return text
    
    def _split_chinese_by_markers(self, text: str) -> List[str]:
        """按中文标记词分句"""
        sentences = []
        
        # 更激进的分句策略
        # 1. 首先按明确的连接词分割
        connection_words = ['然后', '接着', '后来', '于是', '所以', '因此', '但是', '不过', '而且', '另外', '首先', '其次', '最后', '总之']
        
        # 将连接词替换为分隔符
        for word in connection_words:
            text = text.replace(f' {word} ', f' ||{word}|| ')
            text = text.replace(f'{word} ', f'||{word}|| ')
        
        # 按分隔符分割
        parts = text.split('||')
        current_sentence = ""
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            # 如果是连接词，开始新句子
            if part in connection_words:
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = part + " "
            else:
                current_sentence += part + " "
                
                # 如果句子已经足够长，考虑分句
                if len(current_sentence.strip()) > 25:
                    # 检查是否包含自然分句点
                    if any(marker in current_sentence for marker in ['吧', '呢', '啊', '哦', '了']):
                        sentences.append(current_sentence.strip())
                        current_sentence = ""
        
        # 添加剩余内容
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # 进一步细分过长的句子
        final_sentences = []
        for sentence in sentences:
            if len(sentence) > 50:  # 如果句子太长，按逗号或语气词分割
                sub_parts = re.split(r'[，,]|(?<=.{10,})[吧呢啊哦了](?=\s)', sentence)
                for sub_part in sub_parts:
                    if len(sub_part.strip()) > 8:
                        final_sentences.append(sub_part.strip())
            else:
                if len(sentence.strip()) > 8:
                    final_sentences.append(sentence)
        
        return final_sentences or [text.strip()] if text.strip() else []
    
    def _split_english_by_markers(self, text: str) -> List[str]:
        """按英文标记词分句"""
        sentences = []
        
        # 更激进的英文分句策略
        connection_words = ['then', 'next', 'after', 'so', 'therefore', 'but', 'however', 'and', 'also', 'first', 'second', 'finally', 'lastly']
        
        # 将连接词替换为分隔符
        text_lower = text.lower()
        for word in connection_words:
            # 查找连接词的位置（忽略大小写）
            pattern = rf'\b{word}\b'
            matches = list(re.finditer(pattern, text_lower))
            
            # 从后向前替换，避免位置偏移
            for match in reversed(matches):
                start, end = match.span()
                original_word = text[start:end]
                text = text[:start] + f'||{original_word}||' + text[end:]
        
        # 按分隔符分割
        parts = text.split('||')
        current_sentence = ""
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            # 如果是连接词，开始新句子
            if part.lower() in connection_words:
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = part + " "
            else:
                current_sentence += part + " "
                
                # 如果句子已经足够长，考虑分句
                words = current_sentence.strip().split()
                if len(words) > 15:
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
        
        # 添加剩余内容
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # 进一步细分过长的句子
        final_sentences = []
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 20:  # 如果句子太长，按逗号分割
                sub_parts = re.split(r'[,;]', sentence)
                for sub_part in sub_parts:
                    if len(sub_part.strip().split()) > 4:
                        final_sentences.append(sub_part.strip())
            else:
                if len(sentence.strip().split()) > 4:
                    final_sentences.append(sentence)
        
        return final_sentences or [text.strip()] if text.strip() else []
    
    def _add_sentence_punctuation(self, sentence: str, language: str) -> str:
        """为单个句子添加合适的标点符号"""
        if not sentence:
            return sentence
            
        # 移除句尾的停顿词
        sentence = self._remove_filler_words(sentence, language)
        
        if not sentence:
            return ""
        
        # 检查句子类型并添加标点
        if language == 'zh':
            # 中文标点判断
            if any(word in sentence for word in ['什么', '怎么', '为什么', '哪里', '哪个', '谁', '几', '多少', '吗', '呢']):
                if not sentence.endswith('？'):
                    sentence += '？'
            elif any(word in sentence for word in ['太', '真', '好', '哇', '啊', '多么', '非常']):
                if not sentence.endswith('！'):
                    sentence += '！'
            else:
                if not sentence.endswith(('。', '！', '？')):
                    sentence += '。'
        else:
            # 英文标点判断
            sentence_lower = sentence.lower()
            if (sentence_lower.startswith(('what', 'how', 'why', 'where', 'who', 'when', 'which')) or
                any(f' {q} ' in sentence_lower for q in ['do', 'does', 'did', 'is', 'are', 'was', 'were', 'can', 'could', 'would', 'should'])):
                if not sentence.endswith('?'):
                    sentence += '?'
            elif any(word in sentence_lower for word in ['so', 'such', 'what a', 'wow', 'oh', 'amazing', 'wonderful']):
                if not sentence.endswith('!'):
                    sentence += '!'
            else:
                if not sentence.endswith(('.', '!', '?')):
                    sentence += '.'
        
        return sentence
    
    def _remove_filler_words(self, sentence: str, language: str) -> str:
        """移除句尾的停顿词和填充词"""
        if language == 'zh':
            filler_patterns = [
                r'\s*(嗯嗯?|啊啊?|呃|额|那个|这个)\s*$',
                r'\s*(就是说|怎么说|那什么)\s*$'
            ]
        else:
            filler_patterns = [
                r'\s*(um+|uh+|er+|well|you know|I mean)\s*$'
            ]
        
        for pattern in filler_patterns:
            sentence = re.sub(pattern, '', sentence, flags=re.IGNORECASE)
        
        return sentence.strip()
    
    def format_timestamp(self, seconds: float) -> str:
        """
        格式化时间戳为 时:分:秒 格式
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时间戳字符串
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def format_transcript_with_timestamps(self, text: str, segments: List[Dict], title: str = "", language: str = 'auto') -> dict:
        """
        格式化转录文本并添加时间戳
        
        Args:
            text: 原始转录文本
            segments: Whisper返回的段落信息（包含时间戳）
            title: 视频标题
            language: 语言类型
            
        Returns:
            包含时间戳的格式化结果字典
        """
        if not text or not text.strip():
            return {
                'original_text': text,
                'formatted_text': text,
                'timestamped_text': text,
                'language': language,
                'sentence_count': 0,
                'word_count': 0,
                'processing_applied': []
            }
        
        # 检测语言
        if language == 'auto':
            language = self._detect_language(text)
        
        processing_steps = []
        
        # 基于segments创建时间戳文本
        timestamped_sentences = []
        formatted_sentences = []
        
        for segment in segments:
            segment_text = segment.get('text', '').strip()
            start_time = segment.get('start', 0)
            
            if not segment_text:
                continue
            
            # 对每个段落进行分句和标点处理
            sentences = self._split_sentences_improved(segment_text, language)
            
            # 为每个句子分配时间戳（简化版：使用段落开始时间）
            segment_duration = segment.get('end', start_time) - start_time
            sentence_count = len(sentences)
            
            for i, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue
                
                # 计算每个句子的大概时间戳
                sentence_start = start_time + (i * segment_duration / max(sentence_count, 1))
                
                # 添加标点符号
                formatted_sentence = self._add_sentence_punctuation(sentence, language)
                
                # 创建带时间戳的文本
                timestamp = self.format_timestamp(sentence_start)
                timestamped_line = f"[{timestamp}] {formatted_sentence}"
                
                timestamped_sentences.append(timestamped_line)
                formatted_sentences.append(formatted_sentence)
        
        processing_steps.append('添加标点符号')
        processing_steps.append('添加时间戳')
        
        # 合并结果
        timestamped_text = '\n'.join(timestamped_sentences)
        formatted_text = '\n'.join(formatted_sentences)
        
        # 统计信息
        sentence_count = len(formatted_sentences)
        word_count = len(text.split()) if language == 'en' else len(re.sub(r'\s+', '', text))
        
        # 如果有标题，添加到开头
        if title:
            if language == 'zh':
                title_line = f"《{title}》\n"
            else:
                title_line = f'"{title}"\n'
            
            timestamped_text = title_line + timestamped_text
            formatted_text = title_line + formatted_text
            processing_steps.append('添加标题')
        
        return {
            'original_text': text,
            'formatted_text': formatted_text,
            'timestamped_text': timestamped_text,
            'language': language,
            'sentence_count': sentence_count,
            'word_count': word_count,
            'processing_applied': processing_steps
        }
    
    def _process_sentence(self, sentence: str, language: str) -> str:
        """处理单个句子"""
        if not sentence:
            return sentence
            
        # 移除停顿词
        for pause_word in self.pause_indicators:
            if language == 'zh' and any(c in pause_word for c in '嗯啊呃额那个这个'):
                sentence = re.sub(rf'\b{re.escape(pause_word)}\b', '', sentence, flags=re.IGNORECASE)
            elif language == 'en' and pause_word in ['um', 'uh', 'er', 'well', 'you know', 'I mean']:
                sentence = re.sub(rf'\b{re.escape(pause_word)}\b', '', sentence, flags=re.IGNORECASE)
        
        # 清理多余空格
        sentence = re.sub(r'\s+', ' ', sentence.strip())
        
        # 确保句子有合适的长度
        if len(sentence) < 3:
            return sentence
            
        # 检查是否是疑问句
        question_indicators_zh = ['什么', '怎么', '为什么', '哪里', '谁', '多少', '几', '吗', '呢']
        question_indicators_en = ['what', 'how', 'why', 'where', 'who', 'when', 'which', 'do', 'does', 'did', 'is', 'are', 'was', 'were', 'can', 'could', 'would', 'should']
        
        is_question = False
        if language == 'zh':
            is_question = any(indicator in sentence for indicator in question_indicators_zh)
        else:
            # 英文疑问句通常以疑问词开头或包含助动词
            sentence_lower = sentence.lower()
            is_question = (any(sentence_lower.startswith(q) for q in question_indicators_en) or 
                          any(f' {q} ' in sentence_lower for q in question_indicators_en[-8:]))  # 助动词
        
        # 检查是否是感叹句
        exclamation_indicators_zh = ['太', '真', '好', '哇', '啊', '多么']
        exclamation_indicators_en = ['so', 'such', 'what a', 'how', 'wow', 'oh']
        
        is_exclamation = False
        if language == 'zh':
            is_exclamation = any(indicator in sentence for indicator in exclamation_indicators_zh)
        else:
            sentence_lower = sentence.lower()
            is_exclamation = any(indicator in sentence_lower for indicator in exclamation_indicators_en)
        
        return sentence
    
    def format_transcript(self, text: str, title: str = "", language: str = 'auto') -> dict:
        """
        格式化完整的转录文本
        
        Args:
            text: 原始转录文本
            title: 视频标题
            language: 语言类型
            
        Returns:
            格式化后的结果字典
        """
        if not text or not text.strip():
            return {
                'original_text': text,
                'formatted_text': text,
                'language': language,
                'sentence_count': 0,
                'word_count': 0,
                'processing_applied': []
            }
        
        processing_steps = []
        
        # 添加标点符号
        formatted_text = self.add_punctuation(text, language)
        processing_steps.append('添加标点符号')
        
        # 统计信息
        sentences = self._split_sentences(formatted_text, language)
        sentence_count = len(sentences)
        
        word_count = len(text.split()) if language == 'en' else len(re.sub(r'\s+', '', text))
        
        # 如果有标题，添加到开头
        if title:
            if language == 'zh':
                formatted_text = f"《{title}》\n\n{formatted_text}"
            else:
                formatted_text = f'"{title}"\n\n{formatted_text}'
            processing_steps.append('添加标题')
        
        # 段落划分（基于句子数量）
        if sentence_count > 6:
            formatted_text = self._add_paragraphs(formatted_text, language)
            processing_steps.append('段落划分')
        
        return {
            'original_text': text,
            'formatted_text': formatted_text,
            'language': self._detect_language(text) if language == 'auto' else language,
            'sentence_count': sentence_count,
            'word_count': word_count,
            'processing_applied': processing_steps
        }
    
    def _add_paragraphs(self, text: str, language: str) -> str:
        """添加段落分隔"""
        if language == 'zh':
            # 中文每4-5句为一段
            sentences = text.split('。')
            paragraphs = []
            current_paragraph = []
            
            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    current_paragraph.append(sentence.strip())
                    if len(current_paragraph) >= 4 or i == len(sentences) - 1:
                        paragraphs.append('。'.join(current_paragraph) + '。')
                        current_paragraph = []
            
            return '\n\n'.join(paragraphs)
        else:
            # 英文每3-4句为一段
            sentences = text.split('. ')
            paragraphs = []
            current_paragraph = []
            
            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    current_paragraph.append(sentence.strip())
                    if len(current_paragraph) >= 3 or i == len(sentences) - 1:
                        paragraph_text = '. '.join(current_paragraph)
                        if not paragraph_text.endswith('.'):
                            paragraph_text += '.'
                        paragraphs.append(paragraph_text)
                        current_paragraph = []
            
            return '\n\n'.join(paragraphs)


# 使用示例
if __name__ == "__main__":
    processor = TextPostProcessor()
    
    # 测试中文文本
    chinese_text = "你好 这是一个测试 我觉得这个功能很不错 嗯 然后我们可以继续改进"
    result = processor.format_transcript(chinese_text, "测试视频", "zh")
    
    print("中文测试:")
    print("原始文本:", result['original_text'])
    print("格式化文本:", result['formatted_text'])
    print("处理步骤:", result['processing_applied'])
    
    print("\n" + "="*50 + "\n")
    
    # 测试英文文本
    english_text = "hello this is a test I think this feature is really good um then we can continue to improve it"
    result = processor.format_transcript(english_text, "Test Video", "en")
    
    print("英文测试:")
    print("原始文本:", result['original_text'])
    print("格式化文本:", result['formatted_text'])
    print("处理步骤:", result['processing_applied'])