function() {
  const listContainer = document.querySelector(".minutes-module-list");
  if (!listContainer) {
    return {
      error: "未找到逐字稿容器 .minutes-module-list，请确认已经切换到逐字稿标签页。"
    };
  }

  let reactKey = null;
  for (const key in listContainer) {
    if (key.startsWith("__reactFiber$") || key.startsWith("__reactInternalInstance$")) {
      reactKey = key;
      break;
    }
  }

  if (!reactKey) {
    return {
      error: "未找到 React Fiber，页面结构可能已变化。"
    };
  }

  let fiber = listContainer[reactKey];
  let data = null;
  let depth = 0;
  while (fiber && depth < 30) {
    const props = fiber.memoizedProps || fiber.pendingProps;
    if (props && Array.isArray(props.data) && props.data.length > 3) {
      data = props.data;
      break;
    }
    fiber = fiber.return;
    depth += 1;
  }

  if (!data) {
    return {
      error: "未能从 React Fiber 中定位逐字稿数据数组。"
    };
  }

  const items = [];
  const speakers = {};

  for (const item of data) {
    if (!item?.speaker?.user_name) {
      continue;
    }
    if (!item.sentences || item.sentences.length === 0) {
      continue;
    }

    const speakerName = item.speaker.user_name;
    speakers[speakerName] = (speakers[speakerName] || 0) + 1;

    let fullText = "";
    for (const sentence of item.sentences) {
      if (!sentence.words) {
        continue;
      }
      for (const word of sentence.words) {
        fullText += word.text || "";
      }
    }

    if (!fullText.trim()) {
      continue;
    }

    const totalSeconds = Math.floor(item.start_time / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    items.push({
      pid: item.pid,
      speaker: speakerName,
      start_time_ms: item.start_time,
      start_time_formatted: String(minutes).padStart(2, "0") + ":" + String(seconds).padStart(2, "0"),
      text: fullText
    });
  }

  const pageMeta = {};

  const topicSelectors = [
    ".minutes-module-summary-title",
    '[class*="summary-title"]',
    '[class*="meeting-title"]'
  ];
  for (const selector of topicSelectors) {
    const el = document.querySelector(selector);
    if (el?.textContent?.trim()) {
      pageMeta.topic = el.textContent.trim();
      break;
    }
  }

  const bodyText = document.body.innerText;
  if (!pageMeta.topic) {
    const topicMatch = bodyText.match(/会议主题[：:]\s*([^\n]+)/);
    if (topicMatch) {
      pageMeta.topic = topicMatch[1].trim();
    }
  }

  const infoArea = document.querySelector('[class*="header-info"], [class*="record-info"], [class*="meeting-info"]');
  const infoText = infoArea?.innerText || bodyText;

  const organizerMatch = infoText.match(/(?:^|\n)([^\n]+)预定的会议/);
  if (organizerMatch) {
    pageMeta.organizer = organizerMatch[1].trim();
  }

  const timeMatch = infoText.match(/(\d{4}\/\d{2}\/\d{2}\s+\d{2}:\d{2})/);
  if (timeMatch) {
    pageMeta.meetingTime = timeMatch[1];
  }

  const meetingIdMatch = infoText.match(/(\d{3}\s+\d{3}\s+\d{3})/);
  if (meetingIdMatch) {
    pageMeta.meetingId = meetingIdMatch[1];
  }

  return {
    items,
    meta: {
      totalItems: items.length,
      speakers
    },
    pageMeta
  };
};
