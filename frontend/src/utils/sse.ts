// SSE 帧可能跨多个网络块，必须累计到空行后再分派事件。
export function createEventParser(onEvent: (event: string, data: string) => void) {
  let buffer = '' // 保留上一个网络块中尚未结束的事件。
  return (text: string) => {
    buffer += text
    let boundary: RegExpExecArray | null
    while ((boundary = /\r\n\r\n|\n\n|\r\r/.exec(buffer))) {
      const frame = buffer.slice(0, boundary.index)
      buffer = buffer.slice(boundary.index + boundary[0].length)
      let event = 'message'
      const data: string[] = []
      for (const line of frame.split(/\r\n|\n|\r/)) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        if (line.startsWith('data:')) data.push(line.slice(5).replace(/^ /, ''))
      }
      if (data.length) onEvent(event, data.join('\n')) // 忽略心跳注释和无数据帧。
    }
  }
}
